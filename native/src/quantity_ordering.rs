//! 数量极值/范围的流式控制边界；单位数学复用既有固定 Rust 通道。
//! Streaming quantity selection/range boundary; unit math reuses the pinned Rust lane.

use num_rational::BigRational;
use pyo3::basic::CompareOp;
use pyo3::exceptions::{PyBaseException, PyException};
use pyo3::prelude::*;
use std::cmp::Ordering;

use crate::failure::Failure;
use crate::numeric::{Rational, compare_rationals};

type HelperTransport = (
    bool,
    Option<Py<PyAny>>,
    Option<Failure>,
    Option<(&'static str, Py<PyBaseException>, Option<usize>)>,
);

struct Key<'py> {
    exact: Option<BigRational>,
    kind: u8,
    object: Bound<'py, PyAny>,
    powers: Option<Vec<i64>>,
}

struct Session {
    stage: &'static str,
    index: Option<usize>,
    failure: Option<Failure>,
}

impl Session {
    fn new() -> Self {
        Self {
            stage: "iterate",
            index: None,
            failure: None,
        }
    }

    fn key<'py>(
        &mut self,
        py: Python<'py>,
        owner: &Bound<'py, PyAny>,
        prepare: &Bound<'py, PyAny>,
    ) -> PyResult<Option<Key<'py>>> {
        self.stage = "source-unit";
        let unit = owner.getattr(pyo3::intern!(py, "unit"))?;
        self.stage = "source-method";
        let callback = unit.getattr(pyo3::intern!(py, "to_si"))?;
        self.stage = "source-value";
        let value = owner.getattr(pyo3::intern!(py, "value"))?;
        self.stage = "source-key";
        let (success, kind, object, powers): (bool, u8, Bound<'py, PyAny>, Option<Vec<i64>>) =
            prepare.call1(((unit, callback, value),))?.extract()?;
        if !success {
            return Ok(None);
        }
        let exact = match kind {
            0 => Some(object.extract::<PyRef<'_, Rational>>()?.value.clone()),
            1 => {
                let float = object.extract::<f64>()?;
                match BigRational::from_float(float) {
                    Some(value) => Some(value),
                    None => {
                        self.failure = Some(Failure::input(
                            "数量比较需要有限数值 / Quantity comparison requires finite values",
                        ));
                        return Ok(None);
                    }
                }
            }
            2 => None,
            _ => {
                self.failure = Some(Failure::input(
                    "无效数量比较传输 / Invalid quantity comparison transport",
                ));
                return Ok(None);
            }
        };
        Ok(Some(Key {
            exact,
            kind,
            object,
            powers,
        }))
    }

    fn dimension(&mut self, key: &Key<'_>, expected: &mut Option<Vec<i64>>) -> bool {
        self.stage = "dimension";
        if let Some(powers) = &key.powers {
            if powers.len() != 10 || expected.as_ref().is_some_and(|value| value != powers) {
                self.failure = Some(Failure::input(
                    "数量比较的量纲不匹配 / Quantity comparison dimensions do not match",
                ));
                return false;
            }
            if expected.is_none() {
                *expected = Some(powers.clone());
            }
        }
        true
    }

    fn compare(
        &mut self,
        py: Python<'_>,
        left: &Key<'_>,
        right: &Key<'_>,
        operation: CompareOp,
        export: &Bound<'_, PyAny>,
    ) -> PyResult<bool> {
        self.stage = "comparison";
        if let (Some(left), Some(right)) = (&left.exact, &right.exact) {
            // Float64 的已换算结果按精确二进制值参与比较，不把精确域舍入为 float。
            // Compare converted Float64 outputs by their exact binary values, never round exact domains to float.
            let order = py.detach(|| compare_rationals(left, right));
            return Ok(match operation {
                CompareOp::Lt => order == Ordering::Less,
                CompareOp::Gt => order == Ordering::Greater,
                CompareOp::Le => order != Ordering::Greater,
                _ => unreachable!("only strict extrema and inclusive ranges are used"),
            });
        }
        self.stage = "open-key-export";
        let left = if left.kind == 2 {
            left.object.clone()
        } else {
            export.call1((left.kind, &left.object))?
        };
        let right = if right.kind == 2 {
            right.object.clone()
        } else {
            export.call1((right.kind, &right.object))?
        };
        self.stage = "comparison";
        left.rich_compare(&right, operation)?.is_truthy()
    }

    fn finish(
        self,
        py: Python<'_>,
        result: PyResult<Option<Py<PyAny>>>,
    ) -> PyResult<HelperTransport> {
        match result {
            Ok(value) => Ok((value.is_some(), value, self.failure, None)),
            Err(error) if error.is_instance_of::<PyException>(py) => Ok((
                false,
                None,
                None,
                Some((self.stage, error.into_value(py), self.index)),
            )),
            Err(error) => Err(error),
        }
    }
}

#[pyfunction]
#[pyo3(signature = (*, items, maximum, prepare, export))]
pub fn _quantity_extreme(
    py: Python<'_>,
    items: &Bound<'_, PyAny>,
    maximum: bool,
    prepare: &Bound<'_, PyAny>,
    export: &Bound<'_, PyAny>,
) -> PyResult<HelperTransport> {
    let mut session = Session::new();
    let result = (|| {
        let mut iterator = items.try_iter()?;
        let mut best: Option<(Bound<'_, PyAny>, Key<'_>)> = None;
        let mut dimensions = None;
        let mut index = 0usize;
        loop {
            session.stage = "iterate";
            session.index = Some(index);
            let Some(item) = iterator.next() else { break };
            let item = item?;
            let Some(key) = session.key(py, &item, prepare)? else {
                return Ok(None);
            };
            if !session.dimension(&key, &mut dimensions) {
                return Ok(None);
            }
            let replace = match &best {
                None => true,
                Some((_, previous)) => session.compare(
                    py,
                    &key,
                    previous,
                    if maximum {
                        CompareOp::Gt
                    } else {
                        CompareOp::Lt
                    },
                    export,
                )?,
            };
            if replace {
                best = Some((item, key));
            }
            index = match index.checked_add(1) {
                Some(index) => index,
                None => {
                    session.failure = Some(Failure::binding(
                        "OVERFLOW",
                        "数量迭代计数溢出 / Quantity iteration count overflow",
                    ));
                    return Ok(None);
                }
            };
        }
        if best.is_none() {
            session.failure = Some(Failure::input(
                "数量极值需要非空输入 / Quantity extrema require nonempty input",
            ));
        }
        Ok(best.map(|(item, _)| item.unbind()))
    })();
    session.finish(py, result)
}

#[pyfunction]
#[pyo3(signature = (*, bounds, quantity, prepare, export))]
pub fn _quantity_contains(
    py: Python<'_>,
    bounds: &Bound<'_, PyAny>,
    quantity: &Bound<'_, PyAny>,
    prepare: &Bound<'_, PyAny>,
    export: &Bound<'_, PyAny>,
) -> PyResult<HelperTransport> {
    let mut session = Session::new();
    let result = (|| {
        session.index = Some(0);
        session.stage = "lower-bound";
        let lower = bounds.getattr(pyo3::intern!(py, "min_qty"))?;
        let Some(lower) = session.key(py, &lower, prepare)? else {
            return Ok(None);
        };
        session.index = Some(1);
        session.stage = "upper-bound";
        let upper = bounds.getattr(pyo3::intern!(py, "max_qty"))?;
        let Some(upper) = session.key(py, &upper, prepare)? else {
            return Ok(None);
        };
        session.index = Some(2);
        let Some(value) = session.key(py, quantity, prepare)? else {
            return Ok(None);
        };
        let mut dimensions = None;
        for key in [&lower, &upper, &value] {
            if !session.dimension(key, &mut dimensions) {
                return Ok(None);
            }
        }
        let contains = session.compare(py, &lower, &value, CompareOp::Le, export)?
            && session.compare(py, &value, &upper, CompareOp::Le, export)?;
        Ok(Some(
            contains.into_pyobject(py)?.to_owned().into_any().unbind(),
        ))
    })();
    session.finish(py, result)
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::types::PyDict;

    #[test]
    fn exact_comparison_and_original_first_tie_survive_streaming() {
        Python::initialize();
        Python::attach(|py| {
            let scope = PyDict::new(py);
            py.run(c"class Owner:\n unit = type('Unit', (), {'to_si': lambda self, value: value})()\n def __init__(self, value): self.value = value\nfirst = Owner(3)\nsecond = Owner(3)\nitems = iter([first, second])\ndef prepare(parts): return True, 1, float(parts[2]), None\ndef export(kind, value): return value", Some(&scope), None).unwrap();
            let (complete, output, failure, error) = _quantity_extreme(
                py,
                &scope.get_item("items").unwrap().unwrap(),
                false,
                &scope.get_item("prepare").unwrap().unwrap(),
                &scope.get_item("export").unwrap().unwrap(),
            )
            .unwrap();
            assert!(complete && failure.is_none() && error.is_none());
            assert!(
                output
                    .unwrap()
                    .bind(py)
                    .is(scope.get_item("first").unwrap().unwrap())
            );
        });
    }

    #[test]
    fn external_failure_keeps_identity_index_and_traceback() {
        Python::initialize();
        Python::attach(|py| {
            let scope = PyDict::new(py);
            py.run(
                c"error = ValueError('original')\ndef items():\n raise error\n yield None",
                Some(&scope),
                None,
            )
            .unwrap();
            let (_, _, failure, error) = _quantity_extreme(
                py,
                &scope.get_item("items").unwrap().unwrap().call0().unwrap(),
                false,
                &py.None().into_bound(py),
                &py.None().into_bound(py),
            )
            .unwrap();
            assert!(failure.is_none());
            let (stage, error, index) = error.unwrap();
            assert_eq!((stage, index), ("iterate", Some(0)));
            assert!(error.bind(py).is(scope.get_item("error").unwrap().unwrap()));
            assert!(!error.bind(py).getattr("__traceback__").unwrap().is_none());
            assert!(!PyErr::occurred(py));
        });
    }
}
