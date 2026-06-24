"""无符号整数类型。

Unsigned integer type.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, order=True)
class UInteger:
    """无符号整数，基于 Python int 的不可变封装。

    Immutable wrapper around Python int for unsigned integers.

    Attributes:
        value: 底层整数值。/ Underlying integer value.
    """

    value: int

    def __post_init__(self) -> None:
        """校验非负。/ Validate non-negative."""
        if self.value < 0:
            object.__setattr__(self, "value", 0)

    @property
    def zero(self) -> Self:
        """零值。/ Zero value."""
        return self.__class__(0)

    @property
    def one(self) -> Self:
        """单位值。/ One value."""
        return self.__class__(1)

    def copy(self) -> Self:
        """浅复制。/ Shallow copy."""
        return self.__class__(self.value)

    def __add__(self, other: Self) -> Self:
        """加法。/ Addition."""
        return self.__class__(self.value + other.value)

    def __mul__(self, other: Self) -> Self:
        """乘法。/ Multiplication."""
        return self.__class__(self.value * other.value)

    def __sub__(self, other: Self) -> Self:
        """减法（截断到零）。/ Subtraction (clamped to zero)."""
        result = self.value - other.value
        return self.__class__(max(result, 0))

    def __truediv__(self, other: Self) -> Self:
        """整数除法。/ Integer division."""
        if other.value == 0:
            return self.__class__(0)
        return self.__class__(self.value // other.value)

    def __neg__(self) -> Self:
        """取反（无符号截断为零）。/ Negation (unsigned clamps to zero)."""
        return self.__class__(0)

    def __eq__(self, other: object) -> bool:
        """相等比较。/ Equality comparison."""
        if not isinstance(other, UInteger):
            return NotImplemented
        return self.value == other.value

    def __ne__(self, other: object) -> bool:
        """不等比较。/ Inequality comparison."""
        if not isinstance(other, UInteger):
            return NotImplemented
        return self.value != other.value

    def __hash__(self) -> int:
        """哈希值。/ Hash value."""
        return hash(self.value)

    def __repr__(self) -> str:
        """字符串表示。/ String representation."""
        return f"UInteger({self.value})"
