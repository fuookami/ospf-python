"""质因数分解。

Prime factorization.
"""

from __future__ import annotations


def prime_factors(n: int) -> list[int]:
    """对正整数进行质因数分解。

    Perform prime factorization of a positive integer.

    Args:
        n: 待分解的正整数。/ Positive integer to factor.

    Returns:
        质因数列表（可重复）。/
        List of prime factors (may repeat).
    """
    factors: list[int] = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors
