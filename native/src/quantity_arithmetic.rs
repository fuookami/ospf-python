//! 四则的工厂、快照与开放 Python 数值协议控制；单位数学仍归固定 Rust。
//! Factory, snapshot and open Python numeric control; pinned Rust still owns unit math.

use pyo3::exceptions::{PyBaseException, PyException, PyNameError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::PyDict;

type ArithmeticTransport = (
    bool,
    Option<Py<PyAny>>,
    Option<(&'static str, Py<PyBaseException>)>,
);

#[pyfunction]
#[pyo3(signature = (*, owner, other, operation, namespace, builtins, protocols))]
pub fn _quantity_arithmetic(
    py: Python<'_>,
    owner: &Bound<'_, PyAny>,
    other: &Bound<'_, PyAny>,
    operation: &str,
    namespace: &Bound<'_, PyDict>,
    builtins: &Bound<'_, PyDict>,
    protocols: (Bound<'_, PyAny>, Bound<'_, PyAny>),
) -> PyResult<ArithmeticTransport> {
    let (units, compute) = protocols;
    if !matches!(operation, "add" | "subtract" | "multiply" | "divide") {
        return Err(PyValueError::new_err(
            "无效四则选择 / Invalid arithmetic selector",
        ));
    }
    let binary = matches!(operation, "add" | "subtract");
    let mut stage = "factory-lookup";
    let result = (|| {
        let factory = match namespace.get_item("Quantity")? {
            Some(value) => value,
            None => builtins
                .get_item("Quantity")?
                .ok_or_else(|| PyNameError::new_err("name 'Quantity' is not defined"))?,
        };
        stage = "source-unit";
        let left_unit = owner.getattr(pyo3::intern!(py, "unit"))?;
        stage = "other-unit";
        let right_unit = if binary {
            other.getattr(pyo3::intern!(py, "unit"))?
        } else {
            py.None().into_bound(py)
        };
        stage = "unit-snapshot";
        let success: bool = units.call1(((left_unit, right_unit),))?.extract()?;
        if !success {
            return Ok(None);
        }
        stage = "source-value";
        let left = owner.getattr(pyo3::intern!(py, "value"))?;
        stage = "other-value";
        let right = if binary {
            other.getattr(pyo3::intern!(py, "value"))?
        } else {
            other.clone()
        };
        stage = "arithmetic-prepare";
        let (success, native, value, unit): (bool, bool, Bound<'_, PyAny>, Bound<'_, PyAny>) =
            compute.call1(((left.clone(), right.clone()),))?.extract()?;
        if !success {
            return Ok(None);
        }
        stage = "numeric-protocol";
        let value = if native {
            value
        } else {
            match operation {
                "add" => left.add(&right)?,
                "subtract" => left.sub(&right)?,
                "multiply" => left.mul(&right)?,
                "divide" => left.div(&right)?,
                _ => unreachable!("validated operation"),
            }
        };
        stage = "output-unit";
        // 开放单位保持迟读取；原生计算则发布已参与运算的真实输出单位快照。
        // Open units retain late lookup; native math publishes its actual output-unit snapshot.
        let unit = if unit.is_none() {
            owner.getattr(pyo3::intern!(py, "unit"))?
        } else {
            unit
        };
        let keywords = PyDict::new(py);
        keywords.set_item(pyo3::intern!(py, "value"), value)?;
        keywords.set_item(pyo3::intern!(py, "unit"), unit)?;
        stage = "factory-call";
        factory
            .call((), Some(&keywords))
            .map(|value| Some(value.unbind()))
    })();
    match result {
        Ok(value) => Ok((value.is_some(), value, None)),
        Err(error) if error.is_instance_of::<PyException>(py) => {
            Ok((false, None, Some((stage, error.into_value(py)))))
        }
        Err(error) => Err(error),
    }
}
