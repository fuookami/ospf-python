"""区间测试。

Interval tests.

测试 Interval 的创建、包含检查和空区间。
Tests Interval creation, contains check, and empty intervals.
"""

from __future__ import annotations

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
