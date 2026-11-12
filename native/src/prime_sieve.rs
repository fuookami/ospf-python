//! 固定上游素数筛的容量及 Python 传输边界，不复制筛法。 / Capacity and Python transport for the pinned sieve, without another sieve.

use num_bigint::BigInt;
use num_traits::ToPrimitive;
use ospf_rust_math::ordinary::get_primes;
use pyo3::prelude::*;
use pyo3::types::PyInt;

use crate::failure::{Failure, Transport, transport};

fn capacity(limit: usize) -> Result<usize, Failure> {
    // 旧列表需要每槽一个指针；先检查相同容量上界，不设置任意的小输入白名单。
    // Check the former pointer-per-slot capacity ceiling, without an arbitrary small-input allowlist.
    limit
        .checked_add(1)
        .and_then(|slots| slots.checked_mul(std::mem::size_of::<usize>()))
        .filter(|bytes| *bytes <= isize::MAX as usize)
        .ok_or_else(|| {
            Failure::binding(
                "RESOURCE_EXHAUSTED",
                "素数筛容量不可表示 / Prime sieve capacity cannot be represented",
            )
        })
}

fn primes(limit: usize) -> Result<Vec<usize>, Failure> {
    let bytes = capacity(limit)?;
    let mut reservation = Vec::<u8>::new();
    reservation.try_reserve_exact(bytes).map_err(|_| {
        Failure::binding(
            "RESOURCE_EXHAUSTED",
            "无法预留素数筛容量 / Cannot reserve prime sieve capacity",
        )
    })?;
    // 仅为本次容量探测；上游仍唯一拥有进程缓存，预留不保证并发或系统 OOM 可恢复。
    // This is only a per-call capacity probe; upstream alone owns the process cache, with no concurrent/system OOM recovery guarantee.
    drop(reservation);
    Ok(get_primes(limit))
}

/// 仅接收已采集的 exact int，Python 协议由门面调用一次。 / Accept only a collected exact int; the facade calls Python protocols once.
#[pyfunction]
#[pyo3(signature = (*, limit))]
pub(crate) fn _primes_up_to(
    py: Python<'_>,
    limit: &Bound<'_, PyAny>,
) -> PyResult<Transport<Vec<usize>>> {
    if !limit.is_exact_instance_of::<PyInt>() {
        return Ok(transport(Err(Failure::input(
            "素数上界必须是已采集整数 / Prime bound must be a collected integer",
        ))));
    }
    let integer = limit.extract::<BigInt>()?;
    let limit = if integer < BigInt::from(2) {
        0
    } else if let Some(limit) = integer.to_usize() {
        limit
    } else {
        return Ok(transport(Err(Failure::binding(
            "RESOURCE_EXHAUSTED",
            "素数筛长度超出地址空间 / Prime sieve length exceeds address space",
        ))));
    };
    py.check_signals()?;
    let result = py.detach(|| primes(limit));
    py.check_signals()?;
    Ok(transport(result))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn capacity_rejects_unrepresentable_allocations_without_allocating() {
        assert_eq!(capacity(0).unwrap(), std::mem::size_of::<usize>());
        assert_eq!(capacity(1000).unwrap(), 1001 * std::mem::size_of::<usize>());
        assert_eq!(
            capacity(usize::MAX).unwrap_err().category,
            "RESOURCE_EXHAUSTED"
        );
        assert!(capacity(isize::MAX as usize).is_err());
    }

    #[test]
    fn pinned_sieve_is_inclusive_and_detaches_each_output() {
        let mut output = primes(29).unwrap();
        assert_eq!(output, vec![2, 3, 5, 7, 11, 13, 17, 19, 23, 29]);
        output.clear();
        assert_eq!(primes(2).unwrap(), vec![2]);
        assert_eq!(primes(0).unwrap(), Vec::<usize>::new());
    }

    #[test]
    fn pinned_cache_extension_keeps_composite_boundaries() {
        let extended = primes(1100).unwrap();
        assert!(extended.contains(&1009));
        assert!(!extended.contains(&1024));
        assert!(!extended.contains(&1089));
        assert_eq!(primes(10).unwrap(), vec![2, 3, 5, 7]);
    }
}
