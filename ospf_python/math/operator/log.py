"""对数运算符。

Logarithm operators.
"""

from __future__ import annotations

import math


def log_op(x: float) -> float:
    """计算自然对数。

    Compute the natural logarithm.

    Args:
        x: 输入值（正数）。/ Input value (positive).

    Returns:
        ln(x) 的值。/ Value of ln(x).
    """
    return math.log(x)


def log2_op(x: float) -> float:
    """计算以 2 为底的对数。

    Compute the base-2 logarithm.

    Args:
        x: 输入值（正数）。/ Input value (positive).

    Returns:
        log2(x) 的值。/ Value of log2(x).
    """
    return math.log2(x)


def log10_op(x: float) -> float:
    """计算以 10 为底的对数。

    Compute the base-10 logarithm.

    Args:
        x: 输入值（正数）。/ Input value (positive).

    Returns:
        log10(x) 的值。/ Value of log10(x).
    """
    return math.log10(x)
