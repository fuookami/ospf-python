"""区间定义。

Interval definition.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from ospf_python.math.algebra.value_range.bound import (
    Bound,
)

T = TypeVar("T")


@dataclass(frozen=True)
class Interval(Generic[T]):
    """区间，由上下边界定义。

    An interval defined by lower and upper bounds.

    Attributes:
        lower: 下界。/ Lower bound.
        upper: 上界。/ Upper bound.
    """

    lower: Bound[T]
    upper: Bound[T]

    @staticmethod
    def closed(lower: T, upper: T) -> Interval[T]:
        """创建闭区间 [lower, upper]。

        Create a closed interval [lower, upper].

        Args:
            lower: 下界值。/ Lower bound value.
            upper: 上界值。/ Upper bound value.

        Returns:
            闭区间。/ Closed interval.
        """
        return Interval(
            lower=Bound.closed(lower),
            upper=Bound.closed(upper),
        )

    @staticmethod
    def open(lower: T, upper: T) -> Interval[T]:
        """创建开区间 (lower, upper)。

        Create an open interval (lower, upper).

        Args:
            lower: 下界值。/ Lower bound value.
            upper: 上界值。/ Upper bound value.

        Returns:
            开区间。/ Open interval.
        """
        return Interval(
            lower=Bound.open(lower),
            upper=Bound.open(upper),
        )

    @staticmethod
    def open_closed(lower: T, upper: T) -> Interval[T]:
        """创建半开区间 (lower, upper]。

        Create a half-open interval (lower, upper].

        Args:
            lower: 下界值。/ Lower bound value.
            upper: 上界值。/ Upper bound value.

        Returns:
            半开区间。/ Half-open interval.
        """
        return Interval(
            lower=Bound.open(lower),
            upper=Bound.closed(upper),
        )

    @staticmethod
    def closed_open(lower: T, upper: T) -> Interval[T]:
        """创建半闭区间 [lower, upper)。

        Create a half-closed interval [lower, upper).

        Args:
            lower: 下界值。/ Lower bound value.
            upper: 上界值。/ Upper bound value.

        Returns:
            半闭区间。/ Half-closed interval.
        """
        return Interval(
            lower=Bound.closed(lower),
            upper=Bound.open(upper),
        )

    @staticmethod
    def unbounded() -> Interval[T]:
        """创建无界区间 (-inf, +inf)。

        Create an unbounded interval.

        Returns:
            无界区间。/ Unbounded interval.
        """
        return Interval(
            lower=Bound.unbounded(),
            upper=Bound.unbounded(),
        )

    @property
    def is_empty(self) -> bool:
        """区间是否为空。/ Whether the interval is empty."""
        if self.lower.value is not None and self.upper.value is not None:
            if self.lower.value > self.upper.value:  # type: ignore[operator]
                return True
            if self.lower.value == self.upper.value and (
                self.lower.is_open or self.upper.is_open
            ):
                return True
        return False

    def contains(self, value: T) -> bool:
        """检查值是否在区间内。

        Check if a value is within this interval.

        Args:
            value: 待检查的值。/ Value to check.

        Returns:
            是否在区间内。/ Whether in interval.
        """
        # 使用泛型比较 / Use generic comparison
        if self.lower.value is not None:
            if value < self.lower.value:  # type: ignore[operator]
                return False
            if value == self.lower.value and self.lower.is_open:
                return False
        if self.upper.value is not None:
            if value > self.upper.value:  # type: ignore[operator]
                return False
            if value == self.upper.value and self.upper.is_open:
                return False
        return True
