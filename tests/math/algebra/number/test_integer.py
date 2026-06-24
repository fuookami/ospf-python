"""有符号整数类型测试。

Signed integer type tests.

测试 Integer 类的算术、比较和工具方法。
Tests Integer arithmetic, comparison, and utility methods.
"""

from __future__ import annotations

from ospf_python.math.algebra.number.integer import Integer
from ospf_python.utils.functional.ord import Order

# ── Integer creation ────────────────────────────────────────────


class TestIntegerCreation:
    """整数创建测试。"""

    def test_basic_creation(self) -> None:
        """基本创建。/ Basic creation."""
        i = Integer(42)
        assert i.value == 42

    def test_zero_creation(self) -> None:
        """零值创建。/ Zero creation."""
        i = Integer(0)
        assert i.value == 0

    def test_negative_creation(self) -> None:
        """负值创建。/ Negative creation."""
        i = Integer(-7)
        assert i.value == -7


# ── Integer arithmetic ──────────────────────────────────────────


class TestIntegerArithmetic:
    """整数算术测试。"""

    def test_addition(self) -> None:
        """加法。/ Addition."""
        assert Integer(3) + Integer(5) == Integer(8)

    def test_subtraction(self) -> None:
        """减法。/ Subtraction."""
        assert Integer(10) - Integer(3) == Integer(7)

    def test_multiplication(self) -> None:
        """乘法。/ Multiplication."""
        assert Integer(-4) * Integer(5) == Integer(-20)

    def test_negation(self) -> None:
        """取反。/ Negation."""
        assert -Integer(7) == Integer(-7)

    def test_division(self) -> None:
        """整数除法。/ Integer division."""
        assert Integer(10) / Integer(3) == Integer(3)

    def test_division_by_zero(self) -> None:
        """除零返回零。/ Division by zero returns zero."""
        assert Integer(5) / Integer(0) == Integer(0)


# ── Integer comparison ──────────────────────────────────────────


class TestIntegerComparison:
    """整数比较测试。"""

    def test_eq(self) -> None:
        """相等。/ Equal."""
        assert Integer(5) == Integer(5)

    def test_ne(self) -> None:
        """不等。/ Not equal."""
        assert Integer(5) != Integer(3)

    def test_lt(self) -> None:
        """小于。/ Less than."""
        assert Integer(3) < Integer(5)

    def test_gt(self) -> None:
        """大于。/ Greater than."""
        assert Integer(5) > Integer(3)

    def test_cmp_eq(self) -> None:
        """全序比较 EQ。/ Total comparison EQ."""
        assert Integer(5).cmp(Integer(5)) == Order.EQ

    def test_cmp_lt(self) -> None:
        """全序比较 LT。/ Total comparison LT."""
        assert Integer(3).cmp(Integer(5)) == Order.LT

    def test_cmp_gt(self) -> None:
        """全序比较 GT。/ Total comparison GT."""
        assert Integer(5).cmp(Integer(3)) == Order.GT


# ── Integer utilities ───────────────────────────────────────────


class TestIntegerUtilities:
    """整数工具测试。"""

    def test_zero_property(self) -> None:
        """零值属性。/ Zero property."""
        assert Integer(5).zero == Integer(0)

    def test_one_property(self) -> None:
        """单位值属性。/ One property."""
        assert Integer(5).one == Integer(1)

    def test_copy(self) -> None:
        """复制。/ Copy."""
        original = Integer(-99)
        copied = original.copy()
        assert copied == original
        assert copied is not original

    def test_hash(self) -> None:
        """哈希。/ Hash."""
        assert hash(Integer(42)) == hash(Integer(42))

    def test_repr(self) -> None:
        """字符串表示。/ String representation."""
        assert repr(Integer(-3)) == "Integer(-3)"
