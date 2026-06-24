"""减法运算符。

Subtraction operator.
"""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T", int, float)


def minus_op(a: T, b: T) -> T:
    """减法运算。

    Subtraction.

    Args:
        a: 被减数。/ Minuend.
        b: 减数。/ Subtrahend.

    Returns:
        差值。/ Difference.
    """
    return a - b
