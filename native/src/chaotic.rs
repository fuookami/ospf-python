//! Logistic 映射的受限浮点候选。 / Restricted float candidate for the logistic map.

use ospf_rust_math::chaotic::LogisticMap;
use pyo3::prelude::*;
use pyo3::types::PyFloat;

use crate::failure::{Failure, Transport};

fn logistic_float(rate: f64, value: f64) -> f64 {
    LogisticMap::new(rate).step(value)
}

/// 仅接受内置 float，不转换开放数值协议。 / Accept only builtin floats without coercing open numeric protocols.
#[pyfunction]
#[pyo3(signature = (*, rate, value))]
pub(crate) fn _logistic_float64_step<'py>(
    py: Python<'py>,
    rate: &Bound<'py, PyAny>,
    value: &Bound<'py, PyAny>,
) -> PyResult<Transport<Bound<'py, PyAny>>> {
    if !rate.is_exact_instance_of::<PyFloat>() || !value.is_exact_instance_of::<PyFloat>() {
        return Ok((
            None,
            Some(Failure::input(
                "仅支持内置 float / Only builtin float values are supported",
            )),
        ));
    }

    let result = logistic_float(rate.extract()?, value.extract()?);
    // SAFETY: 新引用或 Python 分配错误。 / Returns a new reference or a Python allocation error.
    let result =
        unsafe { Bound::from_owned_ptr_or_err(py, pyo3::ffi::PyFloat_FromDouble(result)) }?;
    Ok((Some(result), None))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn logistic_float_uses_the_pinned_map() {
        assert_eq!(logistic_float(3.9, 0.5), 0.975);
        assert_eq!(logistic_float(4.0, 0.25), 0.75);
        assert!(logistic_float(1.0, f64::NAN).is_nan());
    }
}
