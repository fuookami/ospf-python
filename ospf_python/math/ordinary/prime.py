"""素数相关工具。

Prime number utilities.
"""

from __future__ import annotations

import math


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


def primes_up_to(n: int) -> list[int]:
    """返回不超过 n 的所有素数（埃氏筛）。

    Return all primes up to n (Sieve of Eratosthenes).

    Args:
        n: 上界（含）。/ Upper bound (inclusive).

    Returns:
        素数列表。/ List of primes.
    """
    if n < 2:
        return []
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(math.isqrt(n)) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
    return [i for i, is_p in enumerate(sieve) if is_p]


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
