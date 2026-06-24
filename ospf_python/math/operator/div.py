"""整除运算符。

Integer division operator.
"""

from __future__ import annotations


def div_op(a: int, b: int) -> int:
    """整除运算。

    Integer (floor) division.

    Args:
        a: 被除数。/ Dividend.
        b: 除数。/ Divisor.

    Returns:
        整除结果。/ Floor division result.
    """
    return a // b
