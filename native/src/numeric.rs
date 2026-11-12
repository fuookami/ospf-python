//! 精确域直接使用 ospf-rust-math 的大有理数与运算 traits。 / Bind the upstream big-rational domain and operator traits.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{ToPrimitive, Zero};
use ospf_rust_math::operator::{AddRef, DivRef, MulRef, NegRef, Reciprocal, SubRef};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use serde::Deserialize;
use serde_json::json;
use std::cmp::Ordering;

use crate::failure::{Failure, Transport, transport};

pub(crate) fn compare_rationals(left: &BigRational, right: &BigRational) -> Ordering {
    // 调用方保证正分母；任意精度乘积无整数溢出，且不使用依赖的递归 Ord。 / Callers guarantee positive denominators; arbitrary-precision products cannot overflow integers and avoid the dependency's recursive Ord.
    BigInt::mul_ref(left.numer(), right.denom()).cmp(&BigInt::mul_ref(right.numer(), left.denom()))
}

#[pyclass(frozen, module = "ospf_python._native")]
pub struct Rational {
    pub(crate) value: BigRational,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct WireRational {
    schema: String,
    version: u32,
    numerator: String,
    denominator: String,
}

impl Rational {
    pub(crate) fn create(numerator: BigInt, denominator: BigInt) -> Result<Self, Failure> {
        if denominator.is_zero() {
            return Err(Failure::input(
                "分母不能为零 / Denominator must not be zero",
            ));
        }
        Ok(Self {
            value: BigRational::new(numerator, denominator),
        })
    }

    pub(crate) fn float_value(&self, exact: bool) -> Result<f64, Failure> {
        let value = self
            .value
            .to_f64()
            .filter(|value| value.is_finite())
            .ok_or_else(|| {
                Failure::binding(
                    "OVERFLOW",
                    "超出有限 Float64 范围 / Outside finite Float64 range",
                )
            })?;
        if exact
            && !BigRational::from_float(value)
                .is_some_and(|roundtrip| compare_rationals(&roundtrip, &self.value).is_eq())
        {
            return Err(Failure::binding(
                "DATA_LOSS",
                "Float64 转换丢失精度 / Float64 conversion loses precision",
            ));
        }
        Ok(value)
    }

    fn decode(text: &str) -> Result<Self, Failure> {
        let invalid = || Failure::input("无效有理数快照 / Invalid rational snapshot");
        let wire: WireRational = serde_json::from_str(text).map_err(|_| invalid())?;
        if wire.schema != "ospf.rational" || wire.version != 1 {
            return Err(invalid());
        }
        let parse = |text: &str| -> Result<BigInt, Failure> {
            let integer: BigInt = text.parse().map_err(|_| invalid())?;
            // 只接受规范十进制，避免多种线格式冒充同一快照。 / Require canonical decimal wire integers.
            if integer.to_string() != text {
                return Err(invalid());
            }
            Ok(integer)
        };
        Self::create(parse(&wire.numerator)?, parse(&wire.denominator)?)
    }
}

#[pymethods]
impl Rational {
    fn __copy__(&self) -> Self {
        Self {
            value: self.value.clone(),
        }
    }

    fn __deepcopy__(&self, _memo: &Bound<'_, PyAny>) -> Self {
        self.__copy__()
    }

    fn __reduce__<'py>(&self, py: Python<'py>) -> PyResult<(Bound<'py, PyAny>, (String,))> {
        Ok((
            py.import("ospf_python._native")?
                .getattr("_restore_rational")?,
            (self.to_json(py),),
        ))
    }

    fn as_integer_ratio(&self, py: Python<'_>) -> (BigInt, BigInt) {
        py.detach(|| (self.value.numer().clone(), self.value.denom().clone()))
    }

    fn add(&self, py: Python<'_>, other: &Self) -> Self {
        py.detach(|| Self {
            value: BigRational::add_ref(&self.value, &other.value),
        })
    }

    fn subtract(&self, py: Python<'_>, other: &Self) -> Self {
        py.detach(|| Self {
            value: BigRational::sub_ref(&self.value, &other.value),
        })
    }

    fn multiply(&self, py: Python<'_>, other: &Self) -> Self {
        py.detach(|| Self {
            value: BigRational::mul_ref(&self.value, &other.value),
        })
    }

    fn divide(&self, py: Python<'_>, other: &Self) -> Transport<Self> {
        transport(py.detach(|| {
            if other.value.is_zero() {
                return Err(Failure::input("除数不能为零 / Divisor must not be zero"));
            }
            Ok(Self {
                value: BigRational::div_ref(&self.value, &other.value),
            })
        }))
    }

    fn negated(&self, py: Python<'_>) -> Self {
        py.detach(|| Self {
            value: BigRational::neg_ref(&self.value),
        })
    }

    fn reciprocal(&self, py: Python<'_>) -> Transport<Self> {
        transport(py.detach(|| {
            if self.value.is_zero() {
                return Err(Failure::input("零没有倒数 / Zero has no reciprocal"));
            }
            Ok(Self {
                value: (&self.value).reciprocal(),
            })
        }))
    }

    fn compare(&self, py: Python<'_>, other: &Self) -> i8 {
        py.detach(|| match compare_rationals(&self.value, &other.value) {
            std::cmp::Ordering::Less => -1,
            std::cmp::Ordering::Equal => 0,
            std::cmp::Ordering::Greater => 1,
        })
    }

    #[pyo3(signature = (*, exact=true))]
    fn to_float(&self, py: Python<'_>, exact: bool) -> Transport<f64> {
        transport(py.detach(|| self.float_value(exact)))
    }

    fn to_json(&self, py: Python<'_>) -> String {
        py.detach(|| {
            json!({
                "schema": "ospf.rational",
                "version": 1,
                "numerator": self.value.numer().to_string(),
                "denominator": self.value.denom().to_string(),
            })
            .to_string()
        })
    }
}

#[pyfunction]
#[pyo3(signature = (*, numerator, denominator))]
pub fn _create_rational(
    py: Python<'_>,
    numerator: BigInt,
    denominator: BigInt,
) -> Transport<Rational> {
    transport(py.detach(|| Rational::create(numerator, denominator)))
}

#[pyfunction]
pub fn _rational_from_json(py: Python<'_>, text: &str) -> Transport<Rational> {
    transport(py.detach(|| Rational::decode(text)))
}

// 仅 pickle 的对象恢复入口使用协议异常，普通 JSON API 保持 Result。
// Only pickle object restoration uses protocol exceptions; normal JSON APIs retain Result.
#[pyfunction]
pub fn _restore_rational(py: Python<'_>, text: &str) -> PyResult<Rational> {
    py.detach(|| Rational::decode(text))
        .map_err(|failure| PyValueError::new_err(failure.message))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn copied_rational_and_pickle_decoder_preserve_arbitrary_precision() {
        Python::initialize();
        Python::attach(|py| {
            let original = Rational::create((BigInt::from(1) << 20000) + 1, 17.into()).unwrap();
            assert_eq!(original.value, original.__copy__().value);
            assert_eq!(
                original.value,
                _restore_rational(py, &original.to_json(py)).unwrap().value
            );
            assert!(_restore_rational(py, "{}").is_err());
            assert!(!PyErr::occurred(py));
        });
    }

    #[test]
    fn normalization_and_zero_guard() {
        let value = Rational::create(6.into(), (-8).into()).unwrap();
        assert_eq!(value.value, BigRational::new((-3).into(), 4.into()));
        assert!(Rational::create(1.into(), 0.into()).is_err());
    }

    #[test]
    fn exact_float_policy_includes_underflow() {
        let half = Rational::create(1.into(), 2.into()).unwrap();
        assert_eq!(half.float_value(true).unwrap(), 0.5);
        let third = Rational::create(1.into(), 3.into()).unwrap();
        assert_eq!(third.float_value(true).unwrap_err().category, "DATA_LOSS");
        let tiny = Rational::create(1.into(), BigInt::from(1) << 2000).unwrap();
        assert_eq!(tiny.float_value(true).unwrap_err().category, "DATA_LOSS");
        assert_eq!(tiny.float_value(false).unwrap(), 0.0);
    }

    #[test]
    fn exact_order_has_constant_stack_depth_for_long_continued_fractions() {
        let mut a = BigInt::from(0);
        let mut b = BigInt::from(1);
        for _ in 0..16384 {
            (a, b) = (b.clone(), a + b);
        }
        let next = &a + &b;
        let left = BigRational::new(a, b.clone());
        let right = BigRational::new(b, next);
        assert!(compare_rationals(&left, &right).is_lt());
        assert!(compare_rationals(&right, &left).is_gt());
        assert!(compare_rationals(&left, &left).is_eq());
        assert!(
            compare_rationals(&BigRational::neg_ref(&left), &BigRational::neg_ref(&right)).is_gt()
        );
    }
}
