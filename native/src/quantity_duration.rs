//! Python 有符号微秒时长的表示适配；单位数学仍由固定 Rust quantities 负责。
//! Representation adapter for Python signed microseconds; pinned quantities owns unit math.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{Signed, Zero};
use pyo3::exceptions::{PyBaseException, PyException, PyNameError};
use pyo3::prelude::*;
use pyo3::types::{PyDelta, PyDict};

use crate::failure::Failure;
use crate::numeric::Rational;

type DurationTransport = (
    bool,
    Option<Py<PyAny>>,
    Option<Failure>,
    Option<(&'static str, Py<PyBaseException>)>,
);
const TIME: [i64; 10] = [0, 0, 1, 0, 0, 0, 0, 0, 0, 0];

fn global<'py>(
    name: &'static str,
    namespace: &Bound<'py, PyDict>,
    builtins: &Bound<'py, PyDict>,
) -> PyResult<Bound<'py, PyAny>> {
    match namespace.get_item(name)? {
        Some(value) => Ok(value),
        None => builtins
            .get_item(name)?
            .ok_or_else(|| PyNameError::new_err(format!("name '{name}' is not defined"))),
    }
}

fn finish(
    py: Python<'_>,
    stage: &'static str,
    failure: Option<Failure>,
    result: PyResult<Option<Py<PyAny>>>,
) -> PyResult<DurationTransport> {
    match result {
        Ok(value) => Ok((value.is_some(), value, failure, None)),
        Err(error) if error.is_instance_of::<PyException>(py) => {
            Ok((false, None, None, Some((stage, error.into_value(py)))))
        }
        Err(error) => Err(error),
    }
}

// 只适配精确秒到 Python 微秒，不把 Float64 的 CPython 舍入改为精确二进制舍入。
// Adapt exact seconds only; do not replace CPython Float64 rounding with binary-rational rounding.
fn microseconds(value: &BigRational) -> Result<BigInt, Failure> {
    let numerator = value.numer() * 1_000_000u32;
    let denominator = value.denom();
    let mut whole = &numerator / denominator;
    let remainder = (&numerator % denominator).abs();
    let doubled = remainder * 2u8;
    if doubled > *denominator || (doubled == *denominator && !(&whole % 2u8).is_zero()) {
        whole += if numerator.is_negative() { -1i8 } else { 1i8 };
    }
    let minimum = -BigInt::from(999_999_999u32) * 86_400_000_000u64;
    let maximum = BigInt::from(1_000_000_000u32) * 86_400_000_000u64 - 1u8;
    if whole < minimum || whole > maximum {
        return Err(Failure::binding(
            "OVERFLOW",
            "超出 Python timedelta 的有符号范围 / Outside the signed Python timedelta range",
        ));
    }
    Ok(whole)
}

#[pyfunction]
#[pyo3(signature = (*, value, factor, namespace, builtins, prepare))]
pub fn _quantity_duration_from(
    py: Python<'_>,
    value: &Bound<'_, PyAny>,
    factor: u32,
    namespace: &Bound<'_, PyDict>,
    builtins: &Bound<'_, PyDict>,
    prepare: &Bound<'_, PyAny>,
) -> PyResult<DurationTransport> {
    if !matches!(factor, 60 | 3600) {
        return Ok((
            false,
            None,
            Some(Failure::input("无效时长因子 / Invalid duration factor")),
            None,
        ));
    }
    let mut stage = "factory-lookup";
    let result = (|| {
        let factory = global("Quantity", namespace, builtins)?;
        stage = "constructor-prepare";
        let (success, native, value): (bool, bool, Bound<'_, PyAny>) =
            prepare.call1(((value, factor),))?.extract()?;
        if !success {
            return Ok(None);
        }
        stage = "multiplication";
        let converted = if native { value } else { value.mul(factor)? };
        stage = "unit-lookup";
        let unit = global("SECOND", namespace, builtins)?;
        let keywords = PyDict::new(py);
        keywords.set_item(pyo3::intern!(py, "value"), converted)?;
        keywords.set_item(pyo3::intern!(py, "unit"), unit)?;
        stage = "factory-call";
        factory
            .call((), Some(&keywords))
            .map(|value| Some(value.unbind()))
    })();
    finish(py, stage, None, result)
}

#[pyfunction]
#[pyo3(signature = (*, owner, namespace, builtins, prepare, export))]
pub fn _quantity_to_timedelta(
    py: Python<'_>,
    owner: &Bound<'_, PyAny>,
    namespace: &Bound<'_, PyDict>,
    builtins: &Bound<'_, PyDict>,
    prepare: &Bound<'_, PyAny>,
    export: &Bound<'_, PyAny>,
) -> PyResult<DurationTransport> {
    let mut stage = "source-unit";
    let mut failure = None;
    let result = (|| {
        let unit = owner.getattr(pyo3::intern!(py, "unit"))?;
        stage = "source-method";
        let callback = unit.getattr(pyo3::intern!(py, "to_si"))?;
        stage = "source-value";
        let value = owner.getattr(pyo3::intern!(py, "value"))?;
        stage = "source-call";
        let (success, kind, value, powers): (bool, u8, Bound<'_, PyAny>, Option<Vec<i64>>) =
            prepare.call1(((unit, callback, value),))?.extract()?;
        if !success {
            return Ok(None);
        }
        stage = "dimension";
        if powers
            .as_ref()
            .is_some_and(|powers| powers.as_slice() != TIME)
        {
            failure = Some(Failure::input(
                "时长需要时间量纲 / Duration requires a time dimension",
            ));
            return Ok(None);
        }
        stage = "factory-lookup";
        let factory = global("timedelta", namespace, builtins)?;
        let keywords = PyDict::new(py);
        match kind {
            0 if factory.is(py.get_type::<PyDelta>()) => {
                stage = "microseconds";
                let exact = value.extract::<PyRef<'_, Rational>>()?.value.clone();
                let rounded = match py.detach(|| microseconds(&exact)) {
                    Ok(rounded) => rounded,
                    Err(error) => {
                        failure = Some(error);
                        return Ok(None);
                    }
                };
                keywords.set_item(pyo3::intern!(py, "microseconds"), rounded)?;
            }
            0 => {
                stage = "exact-export";
                keywords.set_item(pyo3::intern!(py, "seconds"), export.call1((value,))?)?;
            }
            1 | 2 => keywords.set_item(pyo3::intern!(py, "seconds"), value)?,
            _ => {
                failure = Some(Failure::input("无效时长传输 / Invalid duration transport"));
                return Ok(None);
            }
        }
        stage = "factory-call";
        factory
            .call((), Some(&keywords))
            .map(|value| Some(value.unbind()))
    })();
    finish(py, stage, failure, result)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_signed_ties_are_even_and_python_bounds_are_asymmetric() {
        for (numerator, expected) in [(1, 0), (3, 2), (5, 2), (7, 4), (-1, 0), (-3, -2), (-5, -2)] {
            assert_eq!(
                microseconds(&BigRational::new(numerator.into(), 2_000_000.into())).unwrap(),
                BigInt::from(expected)
            );
        }
        let minimum = -BigInt::from(999_999_999u32) * 86_400_000_000u64;
        let maximum = BigInt::from(1_000_000_000u32) * 86_400_000_000u64 - 1u8;
        for bound in [&minimum, &maximum] {
            assert_eq!(
                microseconds(&BigRational::new(bound.clone(), 1_000_000.into())).unwrap(),
                *bound
            );
        }
        assert!(microseconds(&BigRational::new(minimum - 1u8, 1_000_000.into())).is_err());
        assert!(microseconds(&BigRational::new(maximum + 1u8, 1_000_000.into())).is_err());
    }

    #[test]
    fn constructor_captures_factory_before_arithmetic_but_unit_after_it() {
        Python::initialize();
        Python::attach(|py| {
            let scope = PyDict::new(py);
            py.run(c"expected = object()\nunit = object()\nQuantity = lambda **kw: expected if kw['unit'] is unit else None\nclass Value:\n def __mul__(self, factor):\n  assert factor == 60\n  globals()['Quantity'] = lambda **kw: None\n  globals()['SECOND'] = unit\n  return self\nvalue = Value()\ndef prepare(parts): return True, False, parts[0]", Some(&scope), None).unwrap();
            let (complete, value, failure, error) = _quantity_duration_from(
                py,
                &scope.get_item("value").unwrap().unwrap(),
                60,
                &scope,
                &PyDict::new(py),
                &scope.get_item("prepare").unwrap().unwrap(),
            )
            .unwrap();
            assert!(complete && failure.is_none() && error.is_none());
            assert!(
                value
                    .unwrap()
                    .bind(py)
                    .is(scope.get_item("expected").unwrap().unwrap())
            );
        });
    }
}
