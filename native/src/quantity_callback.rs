//! 开放单位回调的控制面，不替代固定 Rust 单位内核。
//! Control plane for open unit callbacks, not a replacement unit kernel.

use pyo3::exceptions::{PyBaseException, PyException, PyNameError};
use pyo3::prelude::*;
use pyo3::types::PyDict;

type CallbackTransport = (
    Option<Py<PyAny>>,
    Option<(&'static str, Py<PyBaseException>)>,
);
type DispatchTransport = (
    bool,
    Option<Py<PyAny>>,
    Option<(&'static str, Py<PyBaseException>)>,
);

// 声明顺序就是 Python 局部值的清理顺序，包含失败路径。
// Field order follows Python local-value cleanup, including failure paths.
#[derive(Default)]
struct Locals<'py> {
    standard: Option<Bound<'py, PyAny>>,
    converted: Option<Bound<'py, PyAny>>,
}

fn unary<'py>(
    callable: Bound<'py, PyAny>,
    argument: Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    let result = callable.call1((&argument,));
    // Python CALL 先释放 callable，再释放调用参数。
    // Python CALL releases the callable before its temporary argument.
    drop(callable);
    drop(argument);
    result
}

#[pyfunction]
#[pyo3(signature = (*, owner, target, namespace, builtins))]
pub fn _convert_quantity_callback(
    py: Python<'_>,
    owner: &Bound<'_, PyAny>,
    target: &Bound<'_, PyAny>,
    namespace: &Bound<'_, PyDict>,
    builtins: &Bound<'_, PyDict>,
) -> PyResult<CallbackTransport> {
    let (_, value, error) = convert(py, owner, target, namespace, builtins, None)?;
    Ok((value, error))
}

#[pyfunction]
#[pyo3(signature = (*, owner, target, namespace, builtins, prepare))]
pub fn _convert_quantity_dispatched(
    py: Python<'_>,
    owner: &Bound<'_, PyAny>,
    target: &Bound<'_, PyAny>,
    namespace: &Bound<'_, PyDict>,
    builtins: &Bound<'_, PyDict>,
    prepare: &Bound<'_, PyAny>,
) -> PyResult<DispatchTransport> {
    convert(py, owner, target, namespace, builtins, Some(prepare))
}

fn prepare_callback<'py>(
    prepare: Option<&Bound<'py, PyAny>>,
    unit: &Bound<'py, PyAny>,
    callback: Bound<'py, PyAny>,
    direction: &'static str,
) -> PyResult<(Bound<'py, PyAny>, bool)> {
    match prepare {
        Some(prepare) => prepare.call1((unit, callback, direction))?.extract(),
        None => Ok((callback, false)),
    }
}

fn call_prepared<'py>(
    callback: Bound<'py, PyAny>,
    argument: Bound<'py, PyAny>,
    checked: bool,
) -> PyResult<Option<Bound<'py, PyAny>>> {
    let output = unary(callback, argument)?;
    if checked {
        let (success, value): (bool, Bound<'py, PyAny>) = output.extract()?;
        Ok(success.then_some(value))
    } else {
        Ok(Some(output))
    }
}

fn convert(
    py: Python<'_>,
    owner: &Bound<'_, PyAny>,
    target: &Bound<'_, PyAny>,
    namespace: &Bound<'_, PyDict>,
    builtins: &Bound<'_, PyDict>,
    prepare: Option<&Bound<'_, PyAny>>,
) -> PyResult<DispatchTransport> {
    let mut stage = "source-unit";
    let mut locals = Locals::default();
    let result = (|| {
        let source = owner.getattr(pyo3::intern!(py, "unit"))?;
        stage = "source-method";
        let callback = source.getattr(pyo3::intern!(py, "to_si"));
        let callback = match callback {
            Ok(callback) => {
                stage = "source-prepare";
                prepare_callback(prepare, &source, callback, "source")
            }
            Err(error) => Err(error),
        };
        drop(source);
        let (callback, checked) = callback?;
        stage = "source-value";
        let value = owner.getattr(pyo3::intern!(py, "value"));
        // 即使读取参数失败，也先清理已捕获的 callable。
        // Release the captured callable even when argument lookup fails.
        let value = match value {
            Ok(value) => value,
            Err(error) => {
                drop(callback);
                return Err(error);
            }
        };
        stage = "source-call";
        locals.standard = call_prepared(callback, value, checked)?;
        if locals.standard.is_none() {
            return Ok(None);
        }
        stage = "target-method";
        let callback = target.getattr(pyo3::intern!(py, "from_si"))?;
        stage = "target-prepare";
        let (callback, checked) = prepare_callback(prepare, target, callback, "target")?;
        stage = "target-call";
        locals.converted = call_prepared(
            callback,
            locals
                .standard
                .as_ref()
                .expect("initialized standard")
                .clone(),
            checked,
        )?;
        if locals.converted.is_none() {
            return Ok(None);
        }
        stage = "factory-lookup";
        let factory = match namespace.get_item(pyo3::intern!(py, "Quantity"))? {
            Some(factory) => factory,
            None => builtins
                .get_item(pyo3::intern!(py, "Quantity"))?
                .ok_or_else(|| PyNameError::new_err("name 'Quantity' is not defined"))?,
        };
        stage = "factory-call";
        let keywords = PyDict::new(py);
        keywords.set_item(
            pyo3::intern!(py, "value"),
            locals.converted.as_ref().expect("initialized conversion"),
        )?;
        keywords.set_item(pyo3::intern!(py, "unit"), target)?;
        let result = factory.call((), Some(&keywords));
        drop(factory);
        drop(keywords);
        result.map(|value| Some(value.unbind()))
    })();
    drop(locals);
    match result {
        Ok(value) => Ok((value.is_some(), value, None)),
        Err(error) if error.is_instance_of::<PyException>(py) => {
            // into_value 保留原 traceback，普通 Python tuple 让 GC 看见异常引用。
            // Preserve the traceback; a Python tuple exposes exception edges to GC.
            Ok((false, None, Some((stage, error.into_value(py)))))
        }
        Err(error) => Err(error),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn opaque_values_and_late_factory_are_preserved() {
        Python::initialize();
        Python::attach(|py| {
            let scope = PyDict::new(py);
            py.run(c"class Unit:\n def to_si(self, value):\n  return value\n def from_si(self, value):\n  globals()['Quantity'] = lambda **kw: kw['value']\n  return value\nclass Owner:\n unit = Unit()\n value = object()\nowner = Owner()", Some(&scope), None).unwrap();
            let owner = scope.get_item("owner").unwrap().unwrap();
            let (output, error) = _convert_quantity_callback(
                py,
                &owner,
                &owner.getattr("unit").unwrap(),
                &scope,
                &PyDict::new(py),
            )
            .unwrap();
            assert!(error.is_none());
            assert!(output.unwrap().bind(py).is(owner.getattr("value").unwrap()));
            assert!(!PyErr::occurred(py));
        });
    }

    #[test]
    fn exception_transport_retains_identity_and_traceback() {
        Python::initialize();
        Python::attach(|py| {
            let scope = PyDict::new(py);
            py.run(c"error = ValueError('original')\nclass Owner:\n @property\n def unit(self):\n  raise error\nowner = Owner()", Some(&scope), None).unwrap();
            let (output, failure) = _convert_quantity_callback(
                py,
                &scope.get_item("owner").unwrap().unwrap(),
                &py.None().into_bound(py),
                &scope,
                &PyDict::new(py),
            )
            .unwrap();
            assert!(output.is_none());
            let (stage, error) = failure.unwrap();
            assert_eq!(stage, "source-unit");
            assert!(error.bind(py).is(scope.get_item("error").unwrap().unwrap()));
            assert!(!error.bind(py).getattr("__traceback__").unwrap().is_none());
            assert!(!PyErr::occurred(py));
        });
    }

    #[test]
    fn checked_failure_stops_before_target_or_factory() {
        Python::initialize();
        Python::attach(|py| {
            let scope = PyDict::new(py);
            py.run(c"class Source:\n def to_si(self, value):\n  return value\nclass Owner:\n unit = Source()\n value = 1\nclass Target:\n @property\n def from_si(self):\n  raise AssertionError('target read')\ndef prepare(unit, callback, direction):\n return (lambda value: (False, None)), True\nowner = Owner()\ntarget = Target()", Some(&scope), None).unwrap();
            let (complete, output, error) = _convert_quantity_dispatched(
                py,
                &scope.get_item("owner").unwrap().unwrap(),
                &scope.get_item("target").unwrap().unwrap(),
                &PyDict::new(py),
                &PyDict::new(py),
                &scope.get_item("prepare").unwrap().unwrap(),
            )
            .unwrap();
            assert!(!complete);
            assert!(output.is_none() && error.is_none());
            assert!(!PyErr::occurred(py));
        });
    }

    #[test]
    fn none_factory_output_is_distinct_from_checked_failure() {
        Python::initialize();
        Python::attach(|py| {
            let scope = PyDict::new(py);
            py.run(c"class Unit:\n def to_si(self, value):\n  return value\n def from_si(self, value):\n  return value\nclass Owner:\n unit = Unit()\n value = None\ndef prepare(unit, callback, direction):\n return (lambda value: (True, callback(value))), True\nQuantity = lambda **kw: None\nowner = Owner()", Some(&scope), None).unwrap();
            let owner = scope.get_item("owner").unwrap().unwrap();
            let (complete, output, error) = _convert_quantity_dispatched(
                py,
                &owner,
                &owner.getattr("unit").unwrap(),
                &scope,
                &PyDict::new(py),
                &scope.get_item("prepare").unwrap().unwrap(),
            )
            .unwrap();
            assert!(complete);
            assert!(output.unwrap().is_none(py));
            assert!(error.is_none());
            assert!(!PyErr::occurred(py));
        });
    }
}
