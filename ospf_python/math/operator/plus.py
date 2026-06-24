"""加法运算符。

Addition operator.
"""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T", int, float)


def plus_op(a: T, b: T) -> T:
    """加法运算。

    Addition.

    Args:
        a: 加数。/ First addend.
        b: 加数。/ Second addend.

    Returns:
        和。/ Sum.
    """
    return a + b
