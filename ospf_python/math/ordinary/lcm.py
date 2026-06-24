"""最小公倍数计算。

Least common multiple computation.
"""

from __future__ import annotations

import math


def lcm(a: int, b: int) -> int:
    """计算两个整数的最小公倍数。

    Compute the least common multiple of two integers.

    Args:
        a: 第一个整数。/ First integer.
        b: 第二个整数。/ Second integer.

    Returns:
        最小公倍数。/ Least common multiple.
    """
    return math.lcm(a, b)
