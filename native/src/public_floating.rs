//! 公开浮点 DTO 的计算与外部协议边界。 / Arithmetic and external protocol boundary for the public floating DTO.

use num_bigint::BigInt;
use num_rational::{BigRational, Ratio};
use num_traits::{Signed, ToPrimitive, Zero};
use ospf_rust_math::operator::{AddRef, DivRef, MulRef, NegRef, SubRef};
use pyo3::class::gc::{PyTraverseError, PyVisit};
use pyo3::prelude::*;
use pyo3::types::{PyFloat, PyInt};

use crate::public_integer::{IntegerOps, IntegerRange, integer_range};

/// 只共享原整数边界的 builtin 身份；不保存 DTO、数值或结果。 / Share only builtin identities from the integer boundary, never DTOs, values, or results.
#[pyclass(module = "ospf_python._native", name = "_FloatingOps")]
pub struct FloatingOps {
    integers: IntegerOps,
}

impl FloatingOps {
    pub fn create(py: Python<'_>) -> PyResult<Self> {
        Ok(Self {
            integers: IntegerOps::create(py)?,
        })
    }

    fn arithmetic<'py>(
        &self,
        py: Python<'py>,
        left: &Bound<'py, PyAny>,
        right: &Bound<'py, PyAny>,
        operation: &str,
    ) -> PyResult<Bound<'py, PyAny>> {
        if left.is_exact_instance_of::<PyInt>() && right.is_exact_instance_of::<PyInt>() {
            if operation != "divide" {
                return self
                    .integers
                    .binary(py, left.clone(), right.clone(), operation);
            }
            let value = if let (IntegerRange::Small(left), IntegerRange::Small(right)) =
                (integer_range(left)?, integer_range(right)?)
            {
                if right == 0 {
                    return Err(pyo3::exceptions::PyZeroDivisionError::new_err(
                        "division by zero",
                    ));
                }
                // i64 输入使全部有理数中间值精确落在 i128 内，包含 MIN/-1；未做浮点预舍入。 / i64 inputs keep all rational intermediates exact within i128, including MIN/-1, without float pre-rounding.
                let negative = (left < 0) != (right < 0);
                Ratio::<i128>::div_ref(
                    &Ratio::from_integer(i128::from(left)),
                    &Ratio::from_integer(i128::from(right)),
                )
                .to_f64()
                .map(|value| {
                    if value == 0.0 && negative {
                        -0.0
                    } else {
                        value
                    }
                })
            } else {
                let left = left.extract::<BigInt>()?;
                let right = right.extract::<BigInt>()?;
                if right.is_zero() {
                    return Err(pyo3::exceptions::PyZeroDivisionError::new_err(
                        "division by zero",
                    ));
                }
                py.detach(move || {
                    let negative = left.is_negative() != right.is_negative();
                    let quotient = BigRational::div_ref(
                        &BigRational::from_integer(left),
                        &BigRational::from_integer(right),
                    );
                    quotient.to_f64().map(|value| {
                        if value == 0.0 && negative {
                            -0.0
                        } else {
                            value
                        }
                    })
                })
            };
            return match value {
                Some(value) if value.is_finite() => Ok(value.into_pyobject(py)?.into_any()),
                _ => Err(pyo3::exceptions::PyOverflowError::new_err(
                    "integer division result too large for a float",
                )),
            };
        }
        let builtin_number = |value: &Bound<'_, PyAny>| {
            value.is_exact_instance_of::<PyFloat>() || value.is_exact_instance_of::<PyInt>()
        };
        // 除零文案随解释器版本变化，交由本机数值协议产生。 / Zero-division messages vary by
        // interpreter version, so delegate to the host's numeric protocol.
        if builtin_number(left) && builtin_number(right) {
            let (number_left, number_right) = (left.extract::<f64>()?, right.extract::<f64>()?);
            if operation == "divide" && number_right == 0.0 {
                return left.div(right);
            }
            let result = match operation {
                "add" => f64::add_ref(&number_left, &number_right),
                "subtract" => f64::sub_ref(&number_left, &number_right),
                "multiply" => f64::mul_ref(&number_left, &number_right),
                "divide" => f64::div_ref(&number_left, &number_right),
                _ => unreachable!(),
            };
            return Ok(result.into_pyobject(py)?.into_any());
        }
        // 非 exact 值按其原数值槽派发，不调用 __float__ 或抽取子类载荷。 / Non-exact values keep their numeric slots, without float coercion or subclass payload extraction.
        match operation {
            "add" => left.add(right),
            "subtract" => left.sub(right),
            "multiply" => left.mul(right),
            "divide" => left.div(right),
            _ => unreachable!(),
        }
    }
}

#[pymethods]
impl FloatingOps {
    #[pyo3(signature = (*, owner, other, operation))]
    fn binary<'py>(
        &self,
        py: Python<'py>,
        owner: Bound<'py, PyAny>,
        other: Bound<'py, PyAny>,
        operation: &str,
    ) -> PyResult<Bound<'py, PyAny>> {
        if !matches!(operation, "add" | "subtract" | "multiply" | "divide") {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "无效内部浮点运算 / Invalid internal floating operation",
            ));
        }
        let constructor = owner.getattr(pyo3::intern!(py, "__class__"))?;
        let left = owner.getattr(pyo3::intern!(py, "value"))?;
        let right = other.getattr(pyo3::intern!(py, "value"))?;
        let result = self.arithmetic(py, &left, &right, operation);
        // 与 Python 二元表达式一致，构造前按左、右顺序释放临时操作数。 / Match Python binary-expression operand cleanup, left then right, before construction.
        drop(left);
        drop(right);
        constructor.call1((result?,))
    }

    fn negated<'py>(
        &self,
        py: Python<'py>,
        owner: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let constructor = owner.getattr(pyo3::intern!(py, "__class__"))?;
        let value = owner.getattr(pyo3::intern!(py, "value"))?;
        let result = if value.is_exact_instance_of::<PyFloat>() {
            Ok(f64::neg_ref(&value.extract::<f64>()?)
                .into_pyobject(py)?
                .into_any())
        } else {
            self.integers.negated(py, value.clone())
        };
        drop(value);
        constructor.call1((result?,))
    }

    #[pyo3(signature = (*, left, right, operation))]
    fn relation<'py>(
        &self,
        py: Python<'py>,
        left: Bound<'py, PyAny>,
        right: Bound<'py, PyAny>,
        operation: &str,
    ) -> PyResult<Bound<'py, PyAny>> {
        if left.is_exact_instance_of::<PyFloat>() && right.is_exact_instance_of::<PyFloat>() {
            let left = left.extract::<f64>()?;
            let right = right.extract::<f64>()?;
            let value = match operation {
                "eq" => left == right,
                "ne" => left != right,
                "lt" => left < right,
                "le" => left <= right,
                "gt" => left > right,
                "ge" => left >= right,
                _ => {
                    return Err(pyo3::exceptions::PyValueError::new_err(
                        "无效内部浮点比较 / Invalid internal floating relation",
                    ));
                }
            };
            Ok(value.into_pyobject(py)?.to_owned().into_any())
        } else {
            self.integers.relation(py, left, right, operation)
        }
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.integers.__traverse__(visit)
    }

    fn __clear__(&mut self) {
        self.integers.__clear__();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn same_result(
        py: Python<'_>,
        actual: PyResult<Bound<'_, PyAny>>,
        expected: PyResult<Bound<'_, PyAny>>,
    ) {
        match (actual, expected) {
            (Ok(actual), Ok(expected)) => {
                let actual = actual.extract::<f64>().unwrap();
                let expected = expected.extract::<f64>().unwrap();
                if expected.is_nan() {
                    assert!(actual.is_nan());
                } else {
                    assert_eq!(actual.to_bits(), expected.to_bits());
                }
            }
            (Err(actual), Err(expected)) => {
                assert!(actual.get_type(py).is(expected.get_type(py)));
                assert!(
                    actual
                        .value(py)
                        .getattr("args")
                        .unwrap()
                        .eq(expected.value(py).getattr("args").unwrap())
                        .unwrap()
                );
            }
            _ => panic!("native/Python result mismatch"),
        }
        assert!(!PyErr::occurred(py));
    }

    #[test]
    fn exact_f64_arithmetic_matches_python_ieee_and_zero_errors() {
        Python::initialize();
        Python::attach(|py| {
            let ops = FloatingOps::create(py).unwrap();
            let values = [
                0.0,
                -0.0,
                1.25,
                -3.5,
                f64::MAX,
                f64::MIN_POSITIVE,
                f64::from_bits(1),
                f64::INFINITY,
                f64::NEG_INFINITY,
                f64::NAN,
            ];
            for left in values {
                for right in values {
                    let left = left.into_pyobject(py).unwrap().into_any();
                    let right = right.into_pyobject(py).unwrap().into_any();
                    for operation in ["add", "subtract", "multiply", "divide"] {
                        let expected = match operation {
                            "add" => left.add(&right),
                            "subtract" => left.sub(&right),
                            "multiply" => left.mul(&right),
                            _ => left.div(&right),
                        };
                        same_result(py, ops.arithmetic(py, &left, &right, operation), expected);
                    }
                }
            }
        });
    }

    #[test]
    fn integer_true_division_retains_rounding_overflow_and_signed_underflow() {
        Python::initialize();
        Python::attach(|py| {
            let ops = FloatingOps::create(py).unwrap();
            let mut values = vec![
                BigInt::from(0),
                BigInt::from(1),
                BigInt::from(-1),
                BigInt::from(3),
                BigInt::from(-3),
            ];
            for bits in [53, 63, 64, 1024, 1074, 10000] {
                let value: BigInt = (BigInt::from(1) << bits) + 3;
                values.push(value.clone());
                values.push(-value);
            }
            for left in &values {
                for right in &values {
                    let left = left.into_pyobject(py).unwrap().into_any();
                    let right = right.into_pyobject(py).unwrap().into_any();
                    same_result(
                        py,
                        ops.arithmetic(py, &left, &right, "divide"),
                        left.div(&right),
                    );
                }
            }
        });
    }

    #[test]
    fn bounded_integer_true_division_retains_i64_edges_and_rounding() {
        Python::initialize();
        Python::attach(|py| {
            let ops = FloatingOps::create(py).unwrap();
            let mut values = vec![0, 1, -1, 3, -3, i64::MIN, i64::MAX];
            for bits in [31, 32, 52, 53, 54, 62] {
                let value = 1_i64 << bits;
                for offset in [-3, -1, 0, 1, 3] {
                    values.push(value + offset);
                    values.push(-value - offset);
                }
            }
            for left in &values {
                for right in &values {
                    let left = left.into_pyobject(py).unwrap().into_any();
                    let right = right.into_pyobject(py).unwrap().into_any();
                    same_result(
                        py,
                        ops.arithmetic(py, &left, &right, "divide"),
                        left.div(&right),
                    );
                }
            }
            let mut state = 0xd1b54a32d192ed03_u64;
            for _ in 0..4096 {
                state ^= state << 13;
                state ^= state >> 7;
                state ^= state << 17;
                let left = (state as i64).into_pyobject(py).unwrap().into_any();
                state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
                let right = (state as i64).into_pyobject(py).unwrap().into_any();
                same_result(
                    py,
                    ops.arithmetic(py, &left, &right, "divide"),
                    left.div(&right),
                );
            }
        });
    }

    #[test]
    fn nested_integer_builtin_edges_are_visible_to_python_gc() {
        Python::initialize();
        Python::attach(|py| {
            let ops = Py::new(py, FloatingOps::create(py).unwrap()).unwrap();
            let gc = py.import("gc").unwrap();
            assert!(
                gc.call_method1("is_tracked", (&ops,))
                    .unwrap()
                    .is_truthy()
                    .unwrap()
            );
            let referents = gc.call_method1("get_referents", (&ops,)).unwrap();
            let builtins = py.import("builtins").unwrap();
            // PyO3 还遍历实例的 heap type，不能将其误判为隐藏载荷。 / PyO3 also traverses the instance heap type, not a hidden payload.
            assert_eq!(referents.len().unwrap(), 3);
            assert!(referents.contains(ops.bind(py).get_type()).unwrap());
            assert!(
                referents
                    .contains(builtins.getattr("min").unwrap())
                    .unwrap()
            );
            assert!(
                referents
                    .contains(builtins.getattr("max").unwrap())
                    .unwrap()
            );
            ops.bind(py).borrow_mut().__clear__();
            let cleared = gc.call_method1("get_referents", (&ops,)).unwrap();
            assert_eq!(cleared.len().unwrap(), 1);
            assert!(cleared.get_item(0).unwrap().is(ops.bind(py).get_type()));
        });
    }
}
