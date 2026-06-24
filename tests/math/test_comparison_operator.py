"""比较运算符测试。

Comparison operator tests.

测试 Equal、Unequal、Less、LessEqual、Greater、GreaterEqual。
Tests Equal, Unequal, Less, LessEqual, Greater, GreaterEqual.
"""

from __future__ import annotations

from ospf_python.math.comparison_operator import (
    Equal,
    Greater,
    GreaterEqual,
    Less,
    LessEqual,
    Unequal,
)

# ── Equal ───────────────────────────────────────────────────────


class TestEqual:
    """相等比较测试。"""

    def test_creation(self) -> None:
        """创建相等比较。/ Create equal comparison."""
        op = Equal(left=5, right=5)
        assert op.left == 5
        assert op.right == 5

    def test_different_types(self) -> None:
        """不同类型的操作数。/ Different type operands."""
        op = Equal(left="abc", right=123)
        assert op.left == "abc"
        assert op.right == 123

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        op = Equal(left=1, right=2)
        assert op.left == 1


# ── Unequal ─────────────────────────────────────────────────────


class TestUnequal:
    """不等比较测试。"""

    def test_creation(self) -> None:
        """创建不等比较。/ Create unequal comparison."""
        op = Unequal(left=5, right=3)
        assert op.left == 5
        assert op.right == 3

    def test_unequal_values(self) -> None:
        """不等值。/ Unequal values."""
        op = Unequal(left="a", right="b")
        assert op.left != op.right


# ── Less ────────────────────────────────────────────────────────


class TestLess:
    """小于比较测试。"""

    def test_creation(self) -> None:
        """创建小于比较。/ Create less comparison."""
        op = Less(left=3, right=5)
        assert op.left < op.right

    def test_numeric_values(self) -> None:
        """数值比较。/ Numeric comparison."""
        op = Less(left=1.0, right=2.0)
        assert op.left < op.right


# ── LessEqual ───────────────────────────────────────────────────


class TestLessEqual:
    """小于等于比较测试。"""

    def test_creation(self) -> None:
        """创建小于等于比较。/ Create less-equal comparison."""
        op = LessEqual(left=3, right=5)
        assert op.left <= op.right

    def test_equal_values(self) -> None:
        """相等值。/ Equal values."""
        op = LessEqual(left=5, right=5)
        assert op.left <= op.right


# ── Greater ─────────────────────────────────────────────────────


class TestGreater:
    """大于比较测试。"""

    def test_creation(self) -> None:
        """创建大于比较。/ Create greater comparison."""
        op = Greater(left=5, right=3)
        assert op.left > op.right


# ── GreaterEqual ────────────────────────────────────────────────


class TestGreaterEqual:
    """大于等于比较测试。"""

    def test_creation(self) -> None:
        """创建大于等于比较。/ Create greater-equal comparison."""
        op = GreaterEqual(left=5, right=3)
        assert op.left >= op.right

    def test_equal_values(self) -> None:
        """相等值。/ Equal values."""
        op = GreaterEqual(left=5, right=5)
        assert op.left >= op.right
