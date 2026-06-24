"""数学序列化工具。

Math serialization utilities.
"""

from __future__ import annotations

from fractions import Fraction


def serialize_number(x: int | float | Fraction) -> str:
    """将数值序列化为字符串。

    Serialize a number to string.

    Args:
        x: 待序列化的数值。/ Number to serialize.

    Returns:
        字符串表示。/ String representation.
    """
    if isinstance(x, Fraction):
        return f"{x.numerator}/{x.denominator}"
    return repr(x)


def deserialize_number(s: str) -> int | float | Fraction:
    """从字符串反序列化数值。

    Deserialize a number from string.

    Args:
        s: 数值的字符串表示。/ String representation.

    Returns:
        反序列化后的数值。/ Deserialized number.
    """
    if "/" in s:
        parts = s.split("/", 1)
        return Fraction(int(parts[0]), int(parts[1]))
    if "." in s or "e" in s.lower():
        return float(s)
    return int(s)
