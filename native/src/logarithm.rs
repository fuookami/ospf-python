//! 固定上游对数的输入域适配，不复制对数算法。 / Input-domain adaptation for pinned logarithms, without another logarithm algorithm.

use bigdecimal::BigDecimal;
use num_bigint::BigInt;
use num_traits::{Signed, ToPrimitive, Zero};
use ospf_rust_math::operator::DivRef;
use ospf_rust_math::ordinary::{ln_with_precision, log};
use pyo3::prelude::*;
use pyo3::types::PyInt;

use crate::failure::{Failure, Transport, transport};

enum Operand {
    Float(f64),
    Wide(BigInt),
}

fn operand(value: &Bound<'_, PyAny>) -> PyResult<Result<Operand, Failure>> {
    if value.is_instance_of::<PyInt>() {
        // 与math.log一致，真实int子类读取整数值而不调用其__float__。 / Like math.log, read actual int subclasses without their __float__ hook.
        let integer = value.extract::<BigInt>()?;
        if integer.is_negative() || integer.is_zero() {
            return Ok(Err(domain_failure()));
        }
        Ok(Ok(
            match integer.to_f64().filter(|value| value.is_finite()) {
                Some(value) => Operand::Float(value),
                None => Operand::Wide(integer),
            },
        ))
    } else {
        // PyFloat_AsDouble支持数值协议但不接受float()额外接受的字符串。 / PyFloat_AsDouble accepts numeric protocols, not the strings also accepted by float().
        let value = value.extract::<f64>()?;
        if value <= 0.0 {
            Ok(Err(domain_failure()))
        } else {
            Ok(Ok(Operand::Float(value)))
        }
    }
}

fn domain_failure() -> Failure {
    Failure::input("对数参数必须为正数 / Logarithm arguments must be positive")
}

fn natural(value: Operand) -> Result<f64, Failure> {
    match value {
        Operand::Float(value) => Ok(log(value, std::f64::consts::E)),
        Operand::Wide(value) => {
            // 只把精确整数交给固定上游；不复制其归一化或级数，也不把溢出输入替换为无穷。 / Pass the exact integer to pinned upstream; do not copy normalization/series or replace an overflowing input with infinity.
            ln_with_precision(&BigDecimal::from(value), 64)
                .to_f64()
                .ok_or_else(|| {
                    Failure::binding(
                        "OVERFLOW",
                        "对数结果超出Float64 / Logarithm result exceeds Float64",
                    )
                })
        }
    }
}

fn evaluate(x: Operand, base: Operand) -> Result<f64, Failure> {
    if matches!(base, Operand::Float(1.0)) {
        return Err(Failure::input(
            "对数底数不能为1 / Logarithm base must not be one",
        ));
    }
    match (x, base) {
        (Operand::Float(x), Operand::Float(base)) => Ok(log(x, base)),
        (x, base) => Ok(f64::div_ref(&natural(x)?, &natural(base)?)),
    }
}

/// 按x/base顺序采集并验证，非法x不会触发base协议。 / Collect and validate x/base in order; invalid x never triggers the base protocol.
#[pyfunction]
#[pyo3(signature = (*, x, base))]
pub(crate) fn _log_base(
    py: Python<'_>,
    x: &Bound<'_, PyAny>,
    base: &Bound<'_, PyAny>,
) -> PyResult<Transport<f64>> {
    let x = match operand(x)? {
        Ok(value) => value,
        Err(failure) => return Ok(transport(Err(failure))),
    };
    let base = match operand(base)? {
        Ok(value) => value,
        Err(failure) => return Ok(transport(Err(failure))),
    };
    py.check_signals()?;
    let result = py.detach(move || evaluate(x, base));
    py.check_signals()?;
    Ok(transport(result))
}

#[cfg(test)]
mod tests {
    use super::*;
    use num_traits::One;

    #[test]
    fn finite_values_use_the_pinned_generic_logarithm() {
        for x in [f64::MIN_POSITIVE, 0.5, 1.0, 8.0, f64::MAX] {
            for base in [0.25, 2.0, 10.0, f64::INFINITY] {
                assert_eq!(
                    evaluate(Operand::Float(x), Operand::Float(base))
                        .unwrap()
                        .to_bits(),
                    log(x, base).to_bits()
                );
            }
        }
    }

    #[test]
    fn wide_positive_integers_do_not_become_infinite_inputs() {
        for bits in [1024_usize, 4096] {
            let value = (BigInt::one() << bits) + 123_u8;
            let actual = evaluate(Operand::Wide(value), Operand::Float(2.0)).unwrap();
            assert!((actual - bits as f64).abs() < 1e-10);
        }
        let actual = evaluate(
            Operand::Wide(BigInt::one() << 2048_usize),
            Operand::Wide(BigInt::one() << 4096_usize),
        )
        .unwrap();
        assert!((actual - 0.5).abs() < 1e-14);
    }

    #[test]
    fn nonfinite_values_and_one_base_follow_the_declared_domain() {
        assert!(
            evaluate(Operand::Float(f64::NAN), Operand::Float(2.0))
                .unwrap()
                .is_nan()
        );
        assert!(
            evaluate(Operand::Float(f64::INFINITY), Operand::Float(f64::INFINITY))
                .unwrap()
                .is_nan()
        );
        assert_eq!(
            evaluate(Operand::Float(0.5), Operand::Float(f64::INFINITY))
                .unwrap()
                .to_bits(),
            (-0.0_f64).to_bits()
        );
        assert_eq!(
            evaluate(Operand::Float(f64::NAN), Operand::Float(1.0))
                .unwrap_err()
                .category,
            "ILLEGAL_ARGUMENT"
        );
    }
}
