//! 固定上游初等运算符的输入域适配，不复制数学算法。 / Input-domain adaptation for pinned elementary operators, without another math implementation.

use bigdecimal::BigDecimal;
use num_bigint::BigInt;
use num_traits::{Signed, ToPrimitive, Zero};
use ospf_rust_math::operator::{
    acos, asin, atan, cos, exp, lg, lg_with_precision, lg2, lg2_with_precision, ln,
    ln_with_precision, powf, sin, tan,
};
use pyo3::prelude::*;
use pyo3::types::{PyFloat, PyInt};

use crate::failure::{Failure, Transport, transport};

const LOG_PRECISION: i64 = 64;

#[derive(Clone, Copy, Debug)]
enum Operation {
    Exp,
    Exp2,
    Exp10,
    Ln,
    Log2,
    Log10,
    Sin,
    Cos,
    Tan,
    Asin,
    Acos,
    Atan,
}

impl Operation {
    fn parse(value: &str) -> Result<Self, Failure> {
        match value {
            "exp" => Ok(Self::Exp),
            "exp2" => Ok(Self::Exp2),
            "exp10" => Ok(Self::Exp10),
            "ln" => Ok(Self::Ln),
            "log2" => Ok(Self::Log2),
            "log10" => Ok(Self::Log10),
            "sin" => Ok(Self::Sin),
            "cos" => Ok(Self::Cos),
            "tan" => Ok(Self::Tan),
            "asin" => Ok(Self::Asin),
            "acos" => Ok(Self::Acos),
            "atan" => Ok(Self::Atan),
            _ => Err(Failure::input(
                "未知初等运算符 / Unknown elementary operation",
            )),
        }
    }

    fn is_logarithm(self) -> bool {
        matches!(self, Self::Ln | Self::Log2 | Self::Log10)
    }
}

#[derive(Debug)]
enum Operand {
    Float(f64),
    Wide(BigInt),
}

fn overflow_failure() -> Failure {
    Failure::binding(
        "OVERFLOW",
        "初等运算结果超出Float64 / Elementary operation result exceeds Float64",
    )
}

fn domain_failure() -> Failure {
    Failure::input("初等运算输入超出定义域 / Elementary operation input is outside its domain")
}

fn exact_integer_float(value: &Bound<'_, PyAny>) -> PyResult<Result<f64, Failure>> {
    // 精确 float 直接读载荷：不走 __float__ 协议，也不先做 int 类型判断。
    // 这是最常见的热路径，省掉一次类型检查加一次协议分派。
    // Exact float reads its payload directly: no __float__ protocol dispatch and no prior int type
    // check. This is the hot path, so it saves one type test plus one protocol dispatch.
    if value.is_exact_instance_of::<PyFloat>() {
        return Ok(Ok(value.cast::<PyFloat>()?.value()));
    }
    if value.is_exact_instance_of::<PyInt>() {
        let integer = value.extract::<BigInt>()?;
        return Ok(integer
            .to_f64()
            .filter(|value| value.is_finite())
            .ok_or_else(overflow_failure));
    }
    Ok(Ok(value.extract::<f64>()?))
}

fn power_operand(value: &Bound<'_, PyAny>) -> PyResult<Result<f64, Failure>> {
    if value.is_instance_of::<PyInt>() {
        // 10.0**int 与对数一致读取真实整数载荷，不调用int子类的__float__。 / 10.0**int and logarithms read the actual integer payload rather than an int subclass __float__.
        let integer = value.extract::<BigInt>()?;
        return Ok(integer
            .to_f64()
            .filter(|value| value.is_finite())
            .ok_or_else(overflow_failure));
    }
    Ok(Ok(value.extract::<f64>()?))
}

fn log_operand(value: &Bound<'_, PyAny>) -> PyResult<Result<Operand, Failure>> {
    if value.is_instance_of::<PyInt>() {
        // math.log读取真实int子类载荷而不调用其__float__。 / math.log reads actual int-subclass payloads without __float__.
        let integer = value.extract::<BigInt>()?;
        if integer.is_negative() || integer.is_zero() {
            return Ok(Err(domain_failure()));
        }
        return Ok(Ok(
            match integer.to_f64().filter(|value| value.is_finite()) {
                Some(value) => Operand::Float(value),
                None => Operand::Wide(integer),
            },
        ));
    }
    let value = value.extract::<f64>()?;
    if value.is_nan() {
        return Ok(Ok(Operand::Float(value)));
    }
    if value <= 0.0 {
        return Ok(Err(domain_failure()));
    }
    Ok(Ok(Operand::Float(value)))
}

fn prepare(operation: Operation, value: &Bound<'_, PyAny>) -> PyResult<Result<Operand, Failure>> {
    if operation.is_logarithm() {
        log_operand(value)
    } else if matches!(operation, Operation::Exp10) {
        power_operand(value).map(|result| result.map(Operand::Float))
    } else {
        exact_integer_float(value).map(|result| result.map(Operand::Float))
    }
}

fn wide_log(value: BigInt, operation: Operation) -> Result<f64, Failure> {
    let value = BigDecimal::from(value);
    let output = match operation {
        Operation::Ln => ln_with_precision(&value, LOG_PRECISION),
        Operation::Log2 => lg2_with_precision(&value, LOG_PRECISION),
        Operation::Log10 => lg_with_precision(&value, LOG_PRECISION),
        _ => unreachable!("wide logarithms only accept logarithm operations"),
    }
    .ok_or_else(domain_failure)?
    .to_f64()
    .ok_or_else(overflow_failure)?;
    Ok(output)
}

fn evaluate_float(operation: Operation, value: f64) -> Result<f64, Failure> {
    let output = match operation {
        Operation::Exp => exp(value),
        Operation::Exp2 => powf(2.0_f64, value),
        Operation::Exp10 => powf(10.0_f64, value),
        Operation::Ln if value.is_nan() => value,
        Operation::Ln => return ln(value).ok_or_else(domain_failure),
        Operation::Log2 if value.is_nan() => value,
        Operation::Log2 => return lg2(value).ok_or_else(domain_failure),
        Operation::Log10 if value.is_nan() => value,
        Operation::Log10 => return lg(value).ok_or_else(domain_failure),
        Operation::Sin if value.is_infinite() => return Err(domain_failure()),
        Operation::Sin => sin(value),
        Operation::Cos if value.is_infinite() => return Err(domain_failure()),
        Operation::Cos => cos(value),
        Operation::Tan if value.is_infinite() => return Err(domain_failure()),
        Operation::Tan => return tan(value).ok_or_else(domain_failure),
        Operation::Asin if value.is_nan() => value,
        Operation::Asin => return asin(value).ok_or_else(domain_failure),
        Operation::Acos if value.is_nan() => value,
        Operation::Acos => return acos(value).ok_or_else(domain_failure),
        Operation::Atan => atan(value),
    };
    if value.is_finite() && !output.is_finite() {
        return Err(overflow_failure());
    }
    Ok(output)
}

/// 统一采集12个一元操作，随后在固定上游执行。 / Collect all twelve unary operations, then evaluate in pinned upstream.
#[pyfunction]
#[pyo3(signature = (operation, value))]
pub(crate) fn _elementary_operator(
    py: Python<'_>,
    operation: &str,
    value: &Bound<'_, PyAny>,
) -> PyResult<Transport<f64>> {
    // 成本结构（实测，B261/B263）：本次调用的全部开销都在 FFI 边界上，
    // 数学计算本身是 10–20 ns。因此这里对最常见的 `Operand::Float` 路径：
    //   1. 不再 `py.detach(...)`——为一个 10 ns 的计算释放并重新获取 GIL 是净损失；
    //   2. 不再做两次 Python 级 `check_signals()`——标量一元运算不可能长时间阻塞，
    //      既有合同只在「长遍历」上要求周期性信号检查；
    //   3. 支持位置参数（原来 `(*, ...)` 只接受关键字，每次都要构造并解析 kwargs 字典）。
    // 只有可能较慢的 `Operand::Wide`（BigDecimal 精度对数）才检查一次信号。
    // Cost structure (measured): every nanosecond of overhead is at the FFI boundary; the math is
    // 10-20 ns. So on the common float path this no longer detaches the GIL, no longer performs two
    // Python-level signal checks, and accepts positional arguments instead of a kwargs dict.
    // Only the potentially slower wide (BigDecimal precision) path checks a signal once.
    let operation = match Operation::parse(operation) {
        Ok(operation) => operation,
        Err(failure) => return Ok(transport(Err(failure))),
    };
    let value = match prepare(operation, value)? {
        Ok(value) => value,
        Err(failure) => return Ok(transport(Err(failure))),
    };
    let result = match value {
        Operand::Float(value) => evaluate_float(operation, value),
        Operand::Wide(value) => {
            py.check_signals()?;
            wide_log(value, operation)
        }
    };
    Ok(transport(result))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn bits(value: f64) -> u64 {
        value.to_bits()
    }

    #[test]
    fn exponent_and_trigonometry_delegate_to_the_pinned_operators() {
        assert_eq!(
            bits(evaluate_float(Operation::Exp, 1.0).unwrap()),
            bits(exp(1.0))
        );
        assert_eq!(
            bits(evaluate_float(Operation::Exp2, 0.5).unwrap()),
            bits(powf(2.0_f64, 0.5))
        );
        assert_eq!(
            bits(evaluate_float(Operation::Exp10, 2.0).unwrap()),
            bits(powf(10.0_f64, 2.0))
        );
        assert_eq!(
            bits(evaluate_float(Operation::Sin, 0.5).unwrap()),
            bits(sin(0.5_f64))
        );
        assert_eq!(
            bits(evaluate_float(Operation::Tan, 0.5).unwrap()),
            bits(tan(0.5_f64).unwrap())
        );
    }

    #[test]
    fn finite_overflow_and_nonfinite_domains_are_explicit() {
        assert_eq!(
            evaluate_float(Operation::Exp, f64::MAX)
                .unwrap_err()
                .category,
            "OVERFLOW"
        );
        assert_eq!(
            evaluate_float(Operation::Exp2, 1024.0)
                .unwrap_err()
                .category,
            "OVERFLOW"
        );
        assert_eq!(
            evaluate_float(Operation::Exp10, 1_000.0)
                .unwrap_err()
                .category,
            "OVERFLOW"
        );
        for operation in [Operation::Ln, Operation::Log2, Operation::Log10] {
            assert_eq!(
                evaluate_float(operation, 0.0).unwrap_err().category,
                "ILLEGAL_ARGUMENT"
            );
            assert!(evaluate_float(operation, f64::NAN).unwrap().is_nan());
        }
        for operation in [Operation::Sin, Operation::Cos, Operation::Tan] {
            assert_eq!(
                evaluate_float(operation, f64::INFINITY)
                    .unwrap_err()
                    .category,
                "ILLEGAL_ARGUMENT"
            );
        }
        for operation in [Operation::Asin, Operation::Acos] {
            assert_eq!(
                evaluate_float(operation, 2.0).unwrap_err().category,
                "ILLEGAL_ARGUMENT"
            );
            assert!(evaluate_float(operation, f64::NAN).unwrap().is_nan());
        }
    }

    #[test]
    fn wide_logarithms_remain_exact_inputs() {
        let value = BigInt::from(1) << 4096_usize;
        let log2 = wide_log(value.clone(), Operation::Log2).unwrap();
        assert_eq!(log2, 4096.0);
        assert!(
            (wide_log(value, Operation::Ln).unwrap() - 4096.0 * std::f64::consts::LN_2).abs()
                < 1e-12
        );
    }
}
