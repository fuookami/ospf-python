"""整数幂运算。

Integer power computation.
"""

from __future__ import annotations


def pow_int(base: int, exp: int) -> int:
    """计算整数的整数次幂。

    Compute an integer raised to an integer power.

    Args:
        base: 底数。/ Base.
        exp: 指数（非负）。/ Exponent (non-negative).

    Returns:
        幂运算结果。/ Power result.
    """
    return int(base**exp)
