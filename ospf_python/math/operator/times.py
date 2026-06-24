"""乘法运算符。

Multiplication operator.
"""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T", int, float)


def times_op(a: T, b: T) -> T:
    """乘法运算。

    Multiplication.

    Args:
        a: 乘数。/ First factor.
        b: 乘数。/ Second factor.

    Returns:
        乘积。/ Product.
    """
    return a * b
