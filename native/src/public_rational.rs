//! 公开不可变整数对的计算适配，不持久缓存第二份值。 / Arithmetic adapter for public immutable pairs, without a second persistent value.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{Signed, Zero};
use ospf_rust_math::operator::{AddRef, DivRef, MulRef, NegRef};
use pyo3::class::basic::CompareOp;
use pyo3::prelude::*;
use pyo3::types::PyInt;
use std::cell::Cell;

use crate::numeric::compare_rationals;

thread_local! {
    // 只保存当前构造调用的地址证明，不拥有数值或跨调用缓存。 / Store only address evidence for the current constructor call, never values or a cross-call cache.
    static CANONICAL_INPUT: Cell<Option<(usize, usize)>> = const { Cell::new(None) };
}

struct CanonicalInputScope(Option<(usize, usize)>);

impl CanonicalInputScope {
    fn enter(pair: (usize, usize)) -> Self {
        Self(CANONICAL_INPUT.replace(Some(pair)))
    }

    fn matches(numerator: &Bound<'_, PyAny>, denominator: &Bound<'_, PyAny>) -> bool {
        CANONICAL_INPUT.get() == Some((numerator.as_ptr() as usize, denominator.as_ptr() as usize))
    }
}

impl Drop for CanonicalInputScope {
    fn drop(&mut self) {
        CANONICAL_INPUT.set(self.0);
    }
}

fn publish(
    py: Python<'_>,
    value: (BigInt, BigInt),
    constructor: Option<&Bound<'_, PyAny>>,
) -> PyResult<Py<PyAny>> {
    let n = value.0.into_pyobject(py)?;
    let d = value.1.into_pyobject(py)?;
    match constructor {
        Some(constructor) => {
            // 强引用在作用域内阻止地址复用；不持有借用/锁进入用户构造器。 / Strong references prevent address reuse within the scope; no borrow or lock crosses the user constructor.
            let _scope = CanonicalInputScope::enter((n.as_ptr() as usize, d.as_ptr() as usize));
            constructor.call1((&n, &d)).map(Bound::unbind)
        }
        None => Ok((n, d).into_pyobject(py)?.into_any().unbind()),
    }
}

fn legacy_value(numerator: BigInt, denominator: BigInt) -> BigRational {
    if denominator.is_zero() {
        BigRational::zero()
    } else {
        BigRational::new(numerator, denominator)
    }
}

fn pair(value: BigRational) -> (BigInt, BigInt) {
    value.into_raw()
}

fn operand(numerator: BigInt, denominator: BigInt) -> BigRational {
    // frozen 数据类已规范化正分母；不为临时操作数重复求 gcd。 / Frozen dataclasses already normalized positive denominators; do not recompute gcd for temporary operands.
    if denominator.is_positive() {
        BigRational::new_raw(numerator, denominator)
    } else {
        legacy_value(numerator, denominator)
    }
}

/// 数据类构造校验仍为协议异常；零分母保持旧的短路。 / Dataclass validation retains protocol exceptions and the old zero-denominator short circuit.
#[pyfunction]
pub fn _public_rational_normalize(
    py: Python<'_>,
    numerator: &Bound<'_, PyAny>,
    denominator: &Bound<'_, PyAny>,
) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
    if numerator.is_exact_instance_of::<PyInt>()
        && denominator.is_exact_instance_of::<PyInt>()
        && CanonicalInputScope::matches(numerator, denominator)
    {
        return Ok((numerator.clone().unbind(), denominator.clone().unbind()));
    }
    if denominator.eq(0)? {
        return Ok((
            0i32.into_pyobject(py)?.into_any().unbind(),
            1i32.into_pyobject(py)?.into_any().unbind(),
        ));
    }
    let n = numerator.extract::<BigInt>()?;
    let d = denominator.extract::<BigInt>()?;
    if numerator.is_exact_instance_of::<PyInt>() && denominator.is_exact_instance_of::<PyInt>() {
        let (n, d) = py.detach(|| pair(legacy_value(n, d)));
        return Ok((
            n.into_pyobject(py)?.into_any().unbind(),
            d.into_pyobject(py)?.into_any().unbind(),
        ));
    }
    // Rust 提供约分因子，外部整数仍执行自己的 //、比较和取负协议。 / Rust supplies the reduction factor; external integers keep their //, comparison and negation protocols.
    let gcd = py.detach(|| {
        if d.is_zero() {
            n.abs()
        } else {
            let value = BigRational::new(n, d.clone());
            (d / value.denom()).abs()
        }
    });
    let gcd = gcd.into_pyobject(py)?;
    let n = numerator.floor_div(&gcd)?;
    let d = denominator.floor_div(&gcd)?;
    if d.rich_compare(0, CompareOp::Lt)?.is_truthy()? {
        Ok((n.neg()?.unbind(), d.neg()?.unbind()))
    } else {
        Ok((n.unbind(), d.unbind()))
    }
}

#[pyfunction]
#[pyo3(signature = (*, left, right, operation, constructor=None))]
pub fn _public_rational_binary(
    py: Python<'_>,
    left: (BigInt, BigInt),
    right: (BigInt, BigInt),
    operation: &str,
    constructor: Option<&Bound<'_, PyAny>>,
) -> PyResult<Py<PyAny>> {
    let operation: fn(&BigRational, &BigRational) -> BigRational = match operation {
        "add" => BigRational::add_ref,
        "multiply" => BigRational::mul_ref,
        "divide" => |left, right| {
            if right.is_zero() {
                BigRational::zero()
            } else {
                BigRational::div_ref(left, right)
            }
        },
        _ => {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "无效内部运算 / Invalid internal operation",
            ));
        }
    };
    let value = py.detach(|| {
        pair(operation(
            &operand(left.0, left.1),
            &operand(right.0, right.1),
        ))
    });
    publish(py, value, constructor)
}

#[pyfunction]
#[pyo3(signature = (value, *, constructor=None))]
pub fn _public_rational_negated(
    py: Python<'_>,
    value: (BigInt, BigInt),
    constructor: Option<&Bound<'_, PyAny>>,
) -> PyResult<Py<PyAny>> {
    let value = py.detach(|| {
        let value = BigRational::neg_ref(&operand(value.0, value.1));
        // raw 输入可能来自历史字段恢复；证明必须只授予已约分结果。 / Raw input may come from historical field restoration; certify only reduced results.
        pair(value.reduced())
    });
    publish(py, value, constructor)
}

#[pyfunction]
pub fn _public_rational_less(
    py: Python<'_>,
    left: (BigInt, BigInt),
    right: (BigInt, BigInt),
) -> bool {
    py.detach(|| compare_rationals(&operand(left.0, left.1), &operand(right.0, right.1)).is_lt())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn constructor_evidence_is_nested_thread_local_and_unwind_scoped() {
        assert_eq!(CANONICAL_INPUT.get(), None);
        {
            let _outer = CanonicalInputScope::enter((1, 2));
            {
                let _inner = CanonicalInputScope::enter((3, 4));
                assert_eq!(CANONICAL_INPUT.get(), Some((3, 4)));
                std::thread::spawn(|| assert_eq!(CANONICAL_INPUT.get(), None))
                    .join()
                    .unwrap();
            }
            assert_eq!(CANONICAL_INPUT.get(), Some((1, 2)));
            let failure = std::panic::catch_unwind(|| {
                let _inner = CanonicalInputScope::enter((5, 6));
                panic!("test scoped cleanup");
            });
            assert!(failure.is_err());
            assert_eq!(CANONICAL_INPUT.get(), Some((1, 2)));
        }
        assert_eq!(CANONICAL_INPUT.get(), None);
    }

    #[test]
    fn public_zero_sentinel_does_not_change_the_strict_domain() {
        assert_eq!(legacy_value(5.into(), 0.into()), BigRational::zero());
        assert!(crate::numeric::Rational::create(5.into(), 0.into()).is_err());
    }

    #[test]
    fn snapshots_are_normalized_without_fixed_width_limits() {
        let n = (BigInt::from(1) << 16000) + 1;
        let d = BigInt::from(-17);
        let value = legacy_value(n, d);
        let restored = legacy_value(value.numer().clone(), value.denom().clone());
        assert_eq!(value, restored);
        assert!(restored.denom().is_positive());
    }

    #[test]
    fn temporary_operands_guard_invalid_denominators_without_panicking() {
        assert!(operand(7.into(), 0.into()).is_zero());
        assert_eq!(
            operand(6.into(), (-8).into()),
            legacy_value((-3).into(), 4.into())
        );
        assert_eq!(
            operand(6.into(), 8.into()),
            legacy_value(3.into(), 4.into())
        );
    }
}
