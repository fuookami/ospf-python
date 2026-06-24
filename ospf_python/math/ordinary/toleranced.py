"""容差值类型。

Toleranced value type for approximate comparisons.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Toleranced:
    """带容差的值，支持近似比较。

    A value with tolerance for approximate comparisons.

    Attributes:
        value: 标称值。/ Nominal value.
        tolerance: 容差范围。/ Tolerance range.
    """

    value: float
    tolerance: float

    def __post_init__(self) -> None:
        """校验容差非负。/ Validate tolerance non-negative."""
        if self.tolerance < 0:
            object.__setattr__(self, "tolerance", 0.0)

    @property
    def lower_bound(self) -> float:
        """下界。/ Lower bound."""
        return self.value - self.tolerance

    @property
    def upper_bound(self) -> float:
        """上界。/ Upper bound."""
        return self.value + self.tolerance

    def contains(self, value: float) -> bool:
        """检查值是否在容差范围内。

        Check if a value is within tolerance.

        Args:
            value: 待检查的值。/ Value to check.

        Returns:
            是否在容差内。/ Whether within tolerance.
        """
        return abs(value - self.value) <= self.tolerance

    def overlaps(self, other: Toleranced) -> bool:
        """检查与另一个容差值是否重叠。

        Check if overlaps with another toleranced value.

        Args:
            other: 另一个容差值。/ Other toleranced value.

        Returns:
            是否重叠。/ Whether overlapping.
        """
        return (
            self.lower_bound <= other.upper_bound
            and other.lower_bound <= self.upper_bound
        )

    def __eq__(self, other: object) -> bool:
        """精确相等比较。/ Exact equality comparison."""
        if not isinstance(other, Toleranced):
            return NotImplemented
        return self.value == other.value and self.tolerance == other.tolerance

    def __ne__(self, other: object) -> bool:
        """不等比较。/ Inequality comparison."""
        if not isinstance(other, Toleranced):
            return NotImplemented
        return not self.__eq__(other)

    def __hash__(self) -> int:
        """哈希值。/ Hash value."""
        return hash((self.value, self.tolerance))

    def __repr__(self) -> str:
        """字符串表示。/ String representation."""
        return f"Toleranced({self.value} +- {self.tolerance})"

    def __add__(self, other: Toleranced) -> Toleranced:
        """容差值加法。/ Toleranced addition.

        误差按绝对值传播。
        Tolerances propagate by absolute value.
        """
        return Toleranced(
            value=self.value + other.value,
            tolerance=self.tolerance + other.tolerance,
        )

    def __mul__(self, scalar: float) -> Toleranced:
        """标量乘法。/ Scalar multiplication."""
        return Toleranced(
            value=self.value * scalar,
            tolerance=self.tolerance * abs(scalar),
        )
