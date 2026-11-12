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
        # 决定 3b（2026-11-11 用户裁决 A）：NaN 不是任何值域的成员，边界为 NaN 也同样拒绝。
        # 之前的实现会让 NaN 与任何值比较都为 False，三道闸门全部放过，最后 `return True`，
        # 于是 `ValueWrapper(nan, [0, 10]).is_valid()` 返回 True，且 `[NaN, 10]` 接受 -1e9、
        # `[0, NaN]` 接受 1e9——该侧静默变成无界。
        # Decision 3b: NaN is not a member of any value range, and a NaN bound is rejected too.
        # NaN compares False against everything, so the old gate chain fell through to `return True`.
        if value != value:  # noqa: PLR0124 — NaN 探测 / NaN probe
            return False
        if self.lower.value is not None:
            if self.lower.value != self.lower.value:  # NaN 边界 / NaN bound
                return False
            if value < self.lower.value:  # type: ignore[operator]
                return False
            if value == self.lower.value and self.lower.is_open:
                return False
        if self.upper.value is not None:
            if self.upper.value != self.upper.value:  # NaN 边界 / NaN bound
                return False
            if value > self.upper.value:  # type: ignore[operator]
                return False
            if value == self.upper.value and self.upper.is_open:
                return False
        return True
