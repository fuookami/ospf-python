"""值域类型测试。

Value range type tests.

测试 Bound、Interval、ValueRange、TypedValueRange。
Tests Bound, Interval, ValueRange, TypedValueRange.
"""

from __future__ import annotations

from ospf_python.math.algebra.value_range import (
    Bound,
    BoundType,
    Interval,
    TypedValueRange,
    ValueRange,
)

# ── Bound ─────────────────────────────────────────────────────────


class TestBound:
    """边界类型测试。"""

    def test_closed_bound(self) -> None:
        """闭区间边界。/ Closed bound."""
        b = Bound.closed(5)
        assert b.value == 5
        assert b.is_closed
        assert not b.is_open
        assert not b.is_unbounded

    def test_open_bound(self) -> None:
        """开区间边界。/ Open bound."""
        b = Bound.open(3)
        assert b.value == 3
        assert b.is_open
        assert not b.is_closed

    def test_unbounded(self) -> None:
        """无界。/ Unbounded."""
        b = Bound.unbounded()
        assert b.value is None
        assert b.is_unbounded

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        b = Bound.closed(10)
        assert b.bound_type == BoundType.CLOSED


# ── Interval ──────────────────────────────────────────────────────


class TestInterval:
    """区间测试。"""

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

    def test_open_closed_interval(self) -> None:
        """半开区间 (lower, upper]。/ Half-open interval."""
        iv = Interval.open_closed(0, 10)
        assert not iv.contains(0)
        assert iv.contains(10)
        assert iv.contains(5)

    def test_closed_open_interval(self) -> None:
        """半闭区间 [lower, upper)。/ Half-closed interval."""
        iv = Interval.closed_open(0, 10)
        assert iv.contains(0)
        assert not iv.contains(10)

    def test_unbounded_interval(self) -> None:
        """无界区间。/ Unbounded interval."""
        iv: Interval[int] = Interval.unbounded()
        assert iv.contains(0)
        assert iv.contains(-999)
        assert iv.contains(999)

    def test_empty_interval_inverted(self) -> None:
        """反转区间为空。/ Inverted interval is empty."""
        iv = Interval.closed(10, 5)
        assert iv.is_empty

    def test_empty_open_degenerate(self) -> None:
        """退化开区间为空。/ Degenerate open interval empty."""
        iv = Interval.open(5, 5)
        assert iv.is_empty

    def test_closed_degenerate_not_empty(self) -> None:
        """退化闭区间非空。/ Degenerate closed not empty."""
        iv = Interval.closed(5, 5)
        assert not iv.is_empty
        assert iv.contains(5)

    def test_contains_float(self) -> None:
        """浮点区间包含。/ Float interval contains."""
        iv = Interval.closed(0.0, 1.0)
        assert iv.contains(0.5)
        assert not iv.contains(1.5)


# ── ValueRange ────────────────────────────────────────────────────


class TestValueRange:
    """值域测试。"""

    def test_single_interval_range(self) -> None:
        """单区间值域。/ Single interval range."""
        vr = ValueRange.single(Interval.closed(0, 10))
        assert vr.contains(5)
        assert not vr.contains(15)

    def test_from_value(self) -> None:
        """单值值域。/ Single value range."""
        vr = ValueRange.from_value(42)
        assert vr.contains(42)
        assert not vr.contains(43)

    def test_multiple_intervals(self) -> None:
        """多区间值域。/ Multiple interval range."""
        vr = ValueRange(
            intervals=(
                Interval.closed(0, 5),
                Interval.closed(10, 15),
            )
        )
        assert vr.contains(3)
        assert vr.contains(12)
        assert not vr.contains(7)

    def test_unbounded_range(self) -> None:
        """无界值域。/ Unbounded range."""
        vr: ValueRange[int] = ValueRange.single(Interval.unbounded())
        assert vr.is_unbounded

    def test_empty_range(self) -> None:
        """空值域。/ Empty range."""
        vr = ValueRange.single(Interval.closed(10, 5))
        assert vr.is_empty


# ── TypedValueRange ───────────────────────────────────────────────


class TestTypedValueRange:
    """带类型值域测试。"""

    def test_typed_range(self) -> None:
        """带类型值域。/ Typed range."""
        tvr = TypedValueRange.of(
            "int",
            ValueRange.single(Interval.closed(0, 100)),
        )
        assert tvr.type_name == "int"
        assert tvr.contains(50)

    def test_typed_range_not_contains(self) -> None:
        """带类型值域不包含。/ Typed range not contains."""
        tvr = TypedValueRange.of(
            "int",
            ValueRange.single(Interval.closed(0, 10)),
        )
        assert not tvr.contains(20)
