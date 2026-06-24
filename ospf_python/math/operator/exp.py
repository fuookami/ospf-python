"""指数运算符。

Exponential operators.
"""

from __future__ import annotations

import math


def exp_op(x: float) -> float:
    """计算 e 的 x 次幂。

    Compute e raised to the power of x.

    Args:
        x: 指数。/ Exponent.

    Returns:
        e^x 的值。/ Value of e^x.
    """
    return float(math.exp(x))


def exp2_op(x: float) -> float:
    """计算 2 的 x 次幂。

    Compute 2 raised to the power of x.

    Args:
        x: 指数。/ Exponent.

    Returns:
        2^x 的值。/ Value of 2^x.
    """
    return math.exp2(x)


def exp10_op(x: float) -> float:
    """计算 10 的 x 次幂。

    Compute 10 raised to the power of x.

    Args:
        x: 指数。/ Exponent.

    Returns:
        10^x 的值。/ Value of 10^x.
    """
    return float(10.0**x)
