"""数值转换工具。

Number conversion utilities.
"""

from __future__ import annotations

from fractions import Fraction


def to_float(x: int | float | Fraction) -> float:
    """将数值转换为浮点数。

    Convert a number to float.

    Args:
        x: 输入数值。/ Input number.

    Returns:
        浮点表示。/ Float representation.
    """
    if isinstance(x, Fraction):
        return float(x)
    return float(x)


def to_int(x: int | float | Fraction) -> int:
    """将数值转换为整数（截断）。

    Convert a number to int (truncation).

    Args:
        x: 输入数值。/ Input number.

    Returns:
        整数表示。/ Integer representation.
    """
    if isinstance(x, Fraction):
        return int(x)
    return int(x)


def to_rational(x: int | float | Fraction) -> Fraction:
    """将数值转换为有理数。

    Convert a number to rational (Fraction).

    Args:
        x: 输入数值。/ Input number.

    Returns:
        有理数表示。/ Rational representation.
    """
    if isinstance(x, Fraction):
        return x
    return Fraction(x).limit_denominator()
