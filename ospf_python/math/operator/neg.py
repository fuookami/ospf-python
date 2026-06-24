"""取反运算符。

Negation operator.
"""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T", int, float)


def neg_op(x: T) -> T:
    """取反运算。

    Negation.

    Args:
        x: 输入值。/ Input value.

    Returns:
        相反数。/ Negated value.
    """
    return -x
