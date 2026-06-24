"""无符号数值整数 / Unsigned numeric integer.

对应 Kotlin NumericUInteger。
Mirrors Kotlin NumericUInteger.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NumericUInteger:
    """无符号数值整数 / Unsigned numeric integer.

    Args:
        value: 非负整数值 / Non-negative integer value.
    """

    _value: int

    def __post_init__(self) -> None:
        if self._value < 0:
            raise ValueError("NumericUInteger must be non-negative")

    @property
    def value(self) -> int:
        """获取值 / Get value."""
        return self._value

    def safe_add(self, other: NumericUInteger) -> NumericUInteger:
        """安全加法 / Safe addition."""
        return NumericUInteger(self._value + other._value)

    def safe_mul(self, other: NumericUInteger) -> NumericUInteger:
        """安全乘法 / Safe multiplication."""
        return NumericUInteger(self._value * other._value)

    def __add__(self, other: NumericUInteger) -> NumericUInteger:
        return NumericUInteger(self._value + other._value)

    def __mul__(self, other: NumericUInteger) -> NumericUInteger:
        return NumericUInteger(self._value * other._value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NumericUInteger):
            return NotImplemented
        return self._value == other._value

    def __lt__(self, other: NumericUInteger) -> bool:
        return self._value < other._value

    def __le__(self, other: NumericUInteger) -> bool:
        return self._value <= other._value

    def __hash__(self) -> int:
        return hash(self._value)

    def __str__(self) -> str:
        return str(self._value)
