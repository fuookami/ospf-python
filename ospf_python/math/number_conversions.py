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
    return float(x)


def to_int(x: int | float | Fraction) -> int:
    """将数值转换为整数（截断）。

    Convert a number to int (truncation).

    Args:
        x: 输入数值。/ Input number.

    Returns:
        整数表示。/ Integer representation.
    """
    return int(x)


def to_rational(x: int | float | Fraction) -> Fraction:
    """将数值转换为精确有理数。

    Convert a number to an exact rational (Fraction).

    浮点按其 IEEE 二进制值精确转换，不猜测十进制意图：``0.1`` 得到该二进制值的精确分数，
    而不是 ``1/10``。这与 ``_binding.numeric.Rational.from_float`` 一致。
    A float converts to its exact IEEE binary value without guessing decimal intent: ``0.1``
    yields the exact fraction of that binary value rather than ``1/10``. This matches
    ``_binding.numeric.Rational.from_float``.

    旧实现用 ``Fraction(x).limit_denominator()``，分母上界 1e6，会把小于约 5e-7 的值
    **静默变成 0**，更大精度也被静默截断。
    The old implementation used ``Fraction(x).limit_denominator()`` with the default 1e6
    denominator bound, which silently turned values below about 5e-7 into 0 and silently
    truncated anything finer.

    Args:
        x: 输入数值。/ Input number.

    Returns:
        精确有理数表示。/ Exact rational representation.
    """
    if isinstance(x, Fraction):
        return x
    return Fraction(x)
