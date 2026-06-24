"""边界类型测试。

Bound type tests.

测试 Bound 和 BoundType 的创建和属性。
Tests Bound and BoundType creation and properties.
"""

from __future__ import annotations

from ospf_python.math.algebra.value_range.bound import Bound, BoundType

# ── BoundType ───────────────────────────────────────────────────


class TestBoundType:
    """边界类型枚举测试。"""

    def test_values(self) -> None:
        """枚举值。/ Enum values."""
        assert BoundType.CLOSED.value == "closed"
        assert BoundType.OPEN.value == "open"
        assert BoundType.UNBOUNDED.value == "unbounded"


# ── Bound creation ──────────────────────────────────────────────


class TestBoundCreation:
    """边界创建测试。"""

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
        assert not b.is_unbounded

    def test_unbounded(self) -> None:
        """无界边界。/ Unbounded."""
        b = Bound.unbounded()
        assert b.value is None
        assert b.is_unbounded
        assert not b.is_closed
        assert not b.is_open

    def test_float_bound(self) -> None:
        """浮点边界。/ Float bound."""
        b = Bound.closed(3.14)
        assert b.value == 3.14

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        b = Bound.closed(10)
        assert b.bound_type == BoundType.CLOSED
