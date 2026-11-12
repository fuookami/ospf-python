"""素数相关工具。

Prime number utilities.
"""

from typing import SupportsIndex

from ospf_python._binding.prime_sieve import primes_up_to as _primes_up_to
from ospf_python._binding.result import BindingResult


def is_prime(n: int) -> bool:
    """判断一个正整数是否为素数。

    Check whether a positive integer is prime.

    Args:
        n: 待判断的正整数。/ Positive integer to check.

    Returns:
        是否为素数。/ Whether prime.
    """
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def primes_up_to(n: SupportsIndex) -> BindingResult[list[int]]:
    """以固定 Rust 埃氏筛返回不超过 n 的素数 Result。

    Return a Result of all primes up to n using the pinned Rust sieve.

    Args:
        n: 支持 __index__ 的上界（含）。/ Inclusive bound supporting __index__.

    Returns:
        既有 Result，成功包含独立列表。/ Existing Result containing a detached list.
    """
    return _primes_up_to(n)


def nth_prime(n: int) -> int:
    """返回第 n 个素数（从 1 开始计数）。

    Return the nth prime (1-indexed).

    Args:
        n: 素数序号（从 1 开始）。/
            Prime index (1-indexed).

    Returns:
        第 n 个素数。/ The nth prime.
    """
    count = 0
    candidate = 1
    while count < n:
        candidate += 1
        if is_prime(candidate):
            count += 1
    return candidate
