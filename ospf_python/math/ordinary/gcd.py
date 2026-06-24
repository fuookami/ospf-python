"""最大公约数计算。

Greatest common divisor computation.
"""

from __future__ import annotations

import math


def gcd(a: int, b: int) -> int:
    """计算两个整数的最大公约数。

    Compute the greatest common divisor of two integers.

    Args:
        a: 第一个整数。/ First integer.
        b: 第二个整数。/ Second integer.

    Returns:
        最大公约数。/ Greatest common divisor.
    """
    return math.gcd(a, b)


def extended_gcd(
    a: int,
    b: int,
) -> tuple[int, int, int]:
    """扩展欧几里得算法。

    Extended Euclidean algorithm.

    求解 ax + by = gcd(a, b) 中的 x, y。
    Solves for x, y in ax + by = gcd(a, b).

    Args:
        a: 第一个整数。/ First integer.
        b: 第二个整数。/ Second integer.

    Returns:
        (gcd, x, y) 三元组。/ (gcd, x, y) tuple.
    """
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = extended_gcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)
