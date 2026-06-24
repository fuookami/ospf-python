"""相等性与排序协议测试。

测试 PartialEq、Eq、PartialOrd、Ord 协议的行为。
"""

from __future__ import annotations

from ospf_python.utils.functional import (
    Order,
)


class _Point:
    """测试用点类型，实现 Eq 和 Ord。"""

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __lt__(self, other: _Point) -> bool:
        return (self.x, self.y) < (other.x, other.y)

    def __le__(self, other: _Point) -> bool:
        return (self.x, self.y) <= (other.x, other.y)


class TestPartialEq:
    """PartialEq 协议测试。"""

    def test_reflexive(self) -> None:
        p = _Point(1, 2)
        assert p == p

    def test_symmetric(self) -> None:
        p1 = _Point(1, 2)
        p2 = _Point(1, 2)
        assert (p1 == p2) == (p2 == p1)

    def test_inequality(self) -> None:
        assert _Point(1, 2) != _Point(3, 4)


class TestEq:
    """Eq 协议测试（全等关系）。"""

    def test_eq_is_total(self) -> None:
        """任意两个相同类型的实例都应可比较。"""
        p1 = _Point(0, 0)
        p2 = _Point(1, 1)
        assert (p1 == p2) is not NotImplemented  # type: ignore[comparison-overlap]


class TestPartialOrd:
    """PartialOrd 协议测试。"""

    def test_less_than(self) -> None:
        assert _Point(1, 2) < _Point(3, 4)

    def test_not_less_than_equal(self) -> None:
        assert not (_Point(1, 2) < _Point(1, 2))

    def test_less_or_equal(self) -> None:
        assert _Point(1, 2) <= _Point(1, 2)
        assert _Point(1, 2) <= _Point(3, 4)

    def test_greater_than(self) -> None:
        assert _Point(3, 4) > _Point(1, 2)


class TestOrd:
    """Ord 协议测试（全序关系）。"""

    def test_total_ordering(self) -> None:
        """任意两个同类型实例都应可排序。"""
        points = [_Point(3, 1), _Point(1, 2), _Point(2, 3)]
        result = sorted(points)
        assert result == [
            _Point(1, 2),
            _Point(2, 3),
            _Point(3, 1),
        ]


class TestOrder:
    """Order 枚举测试。"""

    def test_order_values(self) -> None:
        assert Order.LT.value == "lt"
        assert Order.EQ.value == "eq"
        assert Order.GT.value == "gt"

    def test_order_members(self) -> None:
        assert Order("lt") is Order.LT
        assert Order("eq") is Order.EQ
        assert Order("gt") is Order.GT
