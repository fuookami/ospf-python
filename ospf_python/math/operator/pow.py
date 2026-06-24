"""幂运算符。

Power operator.
"""

from __future__ import annotations


def pow_op(base: float, exp: float) -> float:
    """幂运算。

    Exponentiation.

    Args:
        base: 底数。/ Base.
        exp: 指数。/ Exponent.

    Returns:
        base^exp 的值。/ Value of base^exp.
    """
    return float(base**exp)
