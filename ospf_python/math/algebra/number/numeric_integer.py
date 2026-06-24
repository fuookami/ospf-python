"""数值整数（带溢出处理） / Numeric integer with overflow handling.

NumericInteger 类，提供安全算术运算。
NumericInteger class providing safe arithmetic operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class NumericInteger:
    """数值整数 / Numeric integer.

    带溢出处理的整数封装，提供 safe_add 和 safe_mul 方法。
    Integer wrapper with overflow handling, providing safe_add
    and safe_mul methods.

    溢出时结果钳制到 [MIN_VALUE, MAX_VALUE] 范围。
    Results are clamped to [MIN_VALUE, MAX_VALUE] on overflow.

    Attributes:
        _value: 内部整数值。/ Internal int value.
    """

    MIN_VALUE: ClassVar[int] = -(2**63)
    """最小值 / Minimum value."""

    MAX_VALUE: ClassVar[int] = 2**63 - 1
    """最大值 / Maximum value."""

    _value: int = 0

    def __post_init__(self) -> None:
        """钳制值到有效范围。/ Clamp value to valid range."""
        clamped = max(self.MIN_VALUE, min(self.MAX_VALUE, self._value))
        if clamped != self._value:
            object.__setattr__(self, "_value", clamped)

    @property
    def value(self) -> int:
        """获取整数值 / Get int value."""
        return self._value

    # ==================== 安全算术 ====================
    # ==================== Safe arithmetic ====================

    def safe_add(self, other: NumericInteger | int) -> NumericInteger:
        """安全加法（带溢出保护） / Safe addition with overflow protection.

        结果超出范围时钳制到边界值。
        Result is clamped to bounds when out of range.

        Args:
            other: 加数。/ The addend.

        Returns:
            和。/ The sum.
        """
        rhs = other._value if isinstance(other, NumericInteger) else other
        result = self._value + rhs
        clamped = max(self.MIN_VALUE, min(self.MAX_VALUE, result))
        return NumericInteger(clamped)

    def safe_mul(self, other: NumericInteger | int) -> NumericInteger:
        """安全乘法（带溢出保护） / Safe multiplication with overflow protection.

        结果超出范围时钳制到边界值。
        Result is clamped to bounds when out of range.

        Args:
            other: 乘数。/ The multiplier.

        Returns:
            积。/ The product.
        """
        rhs = other._value if isinstance(other, NumericInteger) else other
        result = self._value * rhs
        clamped = max(self.MIN_VALUE, min(self.MAX_VALUE, result))
        return NumericInteger(clamped)

    # ==================== 比较运算 ====================
    # ==================== Comparison ====================

    def __eq__(self, other: object) -> bool:
        """相等比较 / Equality comparison."""
        if isinstance(other, NumericInteger):
            return self._value == other._value
        if isinstance(other, int):
            return self._value == other
        return NotImplemented

    def __lt__(self, other: NumericInteger | int) -> bool:
        """小于比较 / Less than."""
        rhs = other._value if isinstance(other, NumericInteger) else other
        return self._value < rhs

    def __le__(self, other: NumericInteger | int) -> bool:
        """小于等于 / Less than or equal."""
        rhs = other._value if isinstance(other, NumericInteger) else other
        return self._value <= rhs

    def __gt__(self, other: NumericInteger | int) -> bool:
        """大于比较 / Greater than."""
        rhs = other._value if isinstance(other, NumericInteger) else other
        return self._value > rhs

    def __ge__(self, other: NumericInteger | int) -> bool:
        """大于等于 / Greater than or equal."""
        rhs = other._value if isinstance(other, NumericInteger) else other
        return self._value >= rhs

    def __hash__(self) -> int:
        """哈希值 / Hash value."""
        return hash(self._value)

    def __str__(self) -> str:
        """字符串表示 / String representation."""
        return str(self._value)

    def __repr__(self) -> str:
        """开发者表示 / Developer representation."""
        return f"NumericInteger({self._value})"
