//! 固定上游任意精度底数幂的整数/容量适配，不复制快速幂。 / Integer/capacity adaptation for pinned arbitrary-precision-base power, without another power algorithm.

use num_bigint::BigInt;
use num_traits::{One, Signed, ToPrimitive, Zero};
use ospf_rust_math::ordinary::powi;
use pyo3::prelude::*;
use pyo3::types::PyInt;

use crate::failure::{Failure, Transport, transport};

fn resource_failure() -> Failure {
    Failure::binding(
        "RESOURCE_EXHAUSTED",
        "整数幂结果超出计算容量 / Integer power result exceeds computation capacity",
    )
}

fn exponent_for_kernel(base: &BigInt, exponent: &BigInt) -> Result<u64, Failure> {
    if exponent.is_negative() {
        return Err(Failure::input(
            "整数幂指数不能为负数 / Integer power exponent must be nonnegative",
        ));
    }
    // 只对已证明的恒等值规范指数；包括超机器字指数，结果仍调用上游内核生成。
    // Canonicalize only proven identity cases, including wider exponents; upstream still produces the result.
    if exponent.is_zero() || base.is_one() {
        Ok(0)
    } else if base.is_zero() {
        Ok(1)
    } else if base == &-BigInt::one() {
        Ok(u64::from(exponent.bit(0)))
    } else {
        // 非平凡超 u64 指数至少需要 2 EiB 幅值存储，不把指数截断后计算另一道题。
        // A nontrivial exponent beyond u64 needs at least 2 EiB of magnitude storage; never truncate it into a different problem.
        exponent.to_u64().ok_or_else(resource_failure)
    }
}

fn capacity(base_bits: u64, exponent: u64) -> Result<usize, Failure> {
    let bits = u128::from(base_bits) * u128::from(exponent) + 1;
    let bytes = bits.div_ceil(8);
    usize::try_from(bytes)
        .ok()
        .filter(|bytes| *bytes <= isize::MAX as usize)
        .ok_or_else(resource_failure)
}

fn checked_power(base: BigInt, exponent: BigInt) -> Result<BigInt, Failure> {
    let exponent = exponent_for_kernel(&base, &exponent)?;
    let bytes = capacity(base.bits(), exponent)?;
    let mut reservation = Vec::<u8>::new();
    reservation
        .try_reserve_exact(bytes)
        .map_err(|_| resource_failure())?;
    // 仅探测结果幅值上界，未持久镜像数值，也不承诺中间乘积/并发/系统 OOM 可恢复。
    // Probe only an upper bound for magnitude capacity; no persistent value mirror or intermediate/concurrent/system OOM recovery guarantee.
    drop(reservation);
    Ok(powi(base, exponent))
}

/// 仅接收公开边界已采集的两个整数。 / Accept only the two integers already collected by the public boundary.
#[pyfunction]
#[pyo3(signature = (*, base, exponent))]
pub(crate) fn _pow_int(
    py: Python<'_>,
    base: &Bound<'_, PyAny>,
    exponent: &Bound<'_, PyAny>,
) -> PyResult<Transport<BigInt>> {
    if !base.is_exact_instance_of::<PyInt>() || !exponent.is_exact_instance_of::<PyInt>() {
        return Ok(transport(Err(Failure::input(
            "幂参数必须是已采集整数 / Power arguments must be collected integers",
        ))));
    }
    let base = base.extract::<BigInt>()?;
    let exponent = exponent.extract::<BigInt>()?;
    py.check_signals()?;
    let result = py.detach(move || checked_power(base, exponent));
    py.check_signals()?;
    Ok(transport(result))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pinned_generic_power_preserves_large_signed_bases() {
        for base in [
            BigInt::from(-7),
            BigInt::from(3),
            (BigInt::one() << 200_usize) + 123_u8,
        ] {
            for exponent in [0_u32, 1, 2, 3, 41] {
                assert_eq!(
                    checked_power(base.clone(), BigInt::from(exponent)).unwrap(),
                    base.pow(exponent)
                );
            }
        }
    }

    #[test]
    fn arbitrarily_wide_trivial_exponents_are_not_narrowed_or_rejected() {
        let even: BigInt = BigInt::one() << 4096_usize;
        let odd: BigInt = &even + 1_u8;
        assert_eq!(
            checked_power(BigInt::zero(), even.clone()).unwrap(),
            BigInt::zero()
        );
        assert_eq!(
            checked_power(BigInt::one(), odd.clone()).unwrap(),
            BigInt::one()
        );
        assert_eq!(checked_power(-BigInt::one(), even).unwrap(), BigInt::one());
        assert_eq!(checked_power(-BigInt::one(), odd).unwrap(), -BigInt::one());
        assert_eq!(
            checked_power(BigInt::zero(), BigInt::zero()).unwrap(),
            BigInt::one()
        );
    }

    #[test]
    fn invalid_exponents_and_impossible_nontrivial_results_fail_before_power() {
        assert_eq!(
            checked_power(BigInt::zero(), -BigInt::one())
                .unwrap_err()
                .category,
            "ILLEGAL_ARGUMENT"
        );
        assert_eq!(
            checked_power(BigInt::from(2), BigInt::one() << 64)
                .unwrap_err()
                .category,
            "RESOURCE_EXHAUSTED"
        );
    }

    #[test]
    fn checked_capacity_does_not_wrap_its_bit_estimate() {
        assert_eq!(capacity(0, 1).unwrap(), 1);
        assert_eq!(capacity(8, 16).unwrap(), 17);
        assert!(capacity(u64::MAX, u64::MAX).is_err());
    }
}
