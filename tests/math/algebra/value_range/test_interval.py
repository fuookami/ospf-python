"""区间测试。

Interval tests.

测试 Interval 的创建、包含检查和空区间。
Tests Interval creation, contains check, and empty intervals.
"""

from __future__ import annotations

import math

from ospf_python.math.algebra.value_range.interval import Interval

# ── Interval creation ───────────────────────────────────────────


class TestIntervalCreation:
    """区间创建测试。"""

    def test_closed_interval(self) -> None:
        """闭区间。/ Closed interval."""
        iv = Interval.closed(0, 10)
        assert iv.contains(0)
        assert iv.contains(10)
        assert iv.contains(5)

    def test_open_interval(self) -> None:
        """开区间。/ Open interval."""
        iv = Interval.open(0, 10)
        assert not iv.contains(0)
        assert not iv.contains(10)
        assert iv.contains(5)

    def test_open_closed(self) -> None:
        """半开区间 (lower, upper]。/ Half-open interval."""
        iv = Interval.open_closed(0, 10)
        assert not iv.contains(0)
        assert iv.contains(10)

    def test_closed_open(self) -> None:
        """半闭区间 [lower, upper)。/ Half-closed interval."""
        iv = Interval.closed_open(0, 10)
        assert iv.contains(0)
        assert not iv.contains(10)

    def test_unbounded(self) -> None:
        """无界区间。/ Unbounded interval."""
        iv: Interval[int] = Interval.unbounded()
        assert iv.contains(0)
        assert iv.contains(-999)
        assert iv.contains(999)


# ── Interval contains ───────────────────────────────────────────


class TestIntervalContains:
    """区间包含测试。"""

    def test_contains_float(self) -> None:
        """浮点区间包含。/ Float interval contains."""
        iv = Interval.closed(0.0, 1.0)
        assert iv.contains(0.5)
        assert not iv.contains(1.5)

    def test_contains_negative(self) -> None:
        """负区间包含。/ Negative interval contains."""
        iv = Interval.closed(-10, -1)
        assert iv.contains(-5)
        assert not iv.contains(0)


# ── Empty intervals ─────────────────────────────────────────────


class TestEmptyIntervals:
    """空区间测试。"""

    def test_inverted_interval_empty(self) -> None:
        """反转区间为空。/ Inverted interval is empty."""
        iv = Interval.closed(10, 5)
        assert iv.is_empty

    def test_open_degenerate_empty(self) -> None:
        """退化开区间为空。/ Degenerate open interval empty."""
        iv = Interval.open(5, 5)
        assert iv.is_empty

    def test_closed_degenerate_not_empty(self) -> None:
        """退化闭区间非空。/ Degenerate closed not empty."""
        iv = Interval.closed(5, 5)
        assert not iv.is_empty
        assert iv.contains(5)


# ── NaN 不是任何区间的成员（决定 3b）──────────────────────────


class TestNanIsNeverAContainedValue:
    """NaN 既不能作为被检查值，也不能作为边界。 / NaN is never contained and never a usable bound.

    决定 3b（2026-11-11 用户裁决 A）：修复前 NaN 与任何值比较都为 False，
    三道闸门全部放过，`contains` 最后 `return True`，于是
    `ValueWrapper(nan, [0, 10]).is_valid()` 返回 True，且 `[NaN, 10]` 接受 -1e9、
    `[0, NaN]` 接受 1e9——该侧静默变成无界。
    """

    def test_nan_value_is_not_contained(self) -> None:
        """NaN 作为被检查值一律为 False。"""
        interval = Interval.closed(0, 10)
        assert interval.contains(math.nan) is False

    def test_nan_value_is_not_contained_in_unbounded(self) -> None:
        """无界区间同样不包含 NaN。"""
        assert Interval.unbounded().contains(math.nan) is False

    def test_nan_lower_bound_rejects_anything(self) -> None:
        """下界为 NaN 时左侧不再变成无界。"""
        interval = Interval.closed(math.nan, 10)
        assert interval.contains(-1e9) is False
        assert interval.contains(5) is False

    def test_nan_upper_bound_rejects_anything(self) -> None:
        """上界为 NaN 时右侧不再变成无界。"""
        interval = Interval.closed(0, math.nan)
        assert interval.contains(1e9) is False
        assert interval.contains(5) is False

    def test_finite_and_infinite_bounds_still_work(self) -> None:
        """非 NaN 的边界行为不受影响。"""
        assert Interval.closed(0, 10).contains(5) is True
        assert Interval.closed(0, 10).contains(11) is False
        assert Interval.unbounded().contains(1e9) is True
