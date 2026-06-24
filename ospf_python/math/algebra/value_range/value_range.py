"""值域定义。

Value range definition.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from ospf_python.math.algebra.value_range.interval import Interval

T = TypeVar("T")


@dataclass(frozen=True)
class ValueRange(Generic[T]):
    """值域，由一组区间组成。

    A value range consisting of a collection of intervals.

    Attributes:
        intervals: 区间列表。/ List of intervals.
    """

    intervals: tuple[Interval[T], ...]

    @staticmethod
    def single(interval: Interval[T]) -> ValueRange[T]:
        """从单个区间创建值域。

        Create a value range from a single interval.

        Args:
            interval: 单个区间。/ Single interval.

        Returns:
            值域。/ Value range.
        """
        return ValueRange(intervals=(interval,))

    @staticmethod
    def from_value(value: T) -> ValueRange[T]:
        """从单个值创建值域（退化区间）。

        Create a value range from a single value
        (degenerate interval).

        Args:
            value: 单个值。/ Single value.

        Returns:
            值域。/ Value range.
        """
        return ValueRange(intervals=(Interval.closed(value, value),))

    @property
    def is_empty(self) -> bool:
        """值域是否为空。/ Whether the range is empty."""
        return all(interval.is_empty for interval in self.intervals)

    @property
    def is_unbounded(self) -> bool:
        """是否无界。/ Whether unbounded."""
        return any(
            interval.lower.is_unbounded and interval.upper.is_unbounded
            for interval in self.intervals
        )

    def contains(self, value: T) -> bool:
        """检查值是否在值域内。

        Check if a value is within this range.

        Args:
            value: 待检查的值。/ Value to check.

        Returns:
            是否在值域内。/ Whether in range.
        """
        return any(interval.contains(value) for interval in self.intervals)
