"""绝对值运算符。

Absolute value operator.
"""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T", int, float)


def abs_op(x: T) -> T:
    """计算绝对值。

    Compute the absolute value.

    Args:
        x: 输入值。/ Input value.

    Returns:
        绝对值。/ Absolute value.
    """
    return abs(x)
