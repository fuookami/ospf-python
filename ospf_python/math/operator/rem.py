"""取余运算符。

Remainder operator.
"""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T", int, float)


def rem_op(a: T, b: T) -> T:
    """取余运算。

    Remainder (modulo) operation.

    Args:
        a: 被除数。/ Dividend.
        b: 除数。/ Divisor.

    Returns:
        余数。/ Remainder.
    """
    return a % b
