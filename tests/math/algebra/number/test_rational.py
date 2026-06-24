"""有理数类型测试。

Rational number type tests.

测试 Rational 类的算术、比较和分数操作。
Tests Rational arithmetic, comparison, and fraction operations.
"""

from __future__ import annotations

from ospf_python.math.algebra.number.rational import Rational
from ospf_python.utils.functional.ord import Order

# ── Rational creation ───────────────────────────────────────────


class TestRationalCreation:
    """有理数创建测试。"""

    def test_basic_creation(self) -> None:
        """基本创建。/ Basic creation."""
        r = Rational(3, 4)
        assert r.numerator == 3
        assert r.denominator == 4

    def test_auto_reduce(self) -> None:
        """自动约分。/ Auto reduction."""
        r = Rational(4, 8)
        assert r.numerator == 1
        assert r.denominator == 2

    def test_negative_denominator(self) -> None:
        """负分母标准化。/ Negative denominator normalized."""
        r = Rational(1, -2)
        assert r.numerator == -1
        assert r.denominator == 2

    def test_zero_denominator(self) -> None:
        """零分母处理。/ Zero denominator handling."""
        r = Rational(5, 0)
        assert r == Rational(0)

    def test_integer_rational(self) -> None:
        """整数有理数。/ Integer rational."""
        r = Rational(5, 1)
        assert r.numerator == 5
        assert r.denominator == 1


# ── Rational arithmetic ─────────────────────────────────────────


class TestRationalArithmetic:
    """有理数算术测试。"""

    def test_addition(self) -> None:
        """加法。/ Addition."""
        result = Rational(1, 2) + Rational(1, 3)
        assert result == Rational(5, 6)

    def test_subtraction(self) -> None:
        """减法。/ Subtraction."""
        result = Rational(3, 4) - Rational(1, 4)
        assert result == Rational(1, 2)

    def test_multiplication(self) -> None:
        """乘法。/ Multiplication."""
        result = Rational(2, 3) * Rational(3, 4)
        assert result == Rational(1, 2)

    def test_division(self) -> None:
        """除法。/ Division."""
        result = Rational(1, 2) / Rational(1, 4)
        assert result == Rational(2, 1)

    def test_negation(self) -> None:
        """取反。/ Negation."""
        assert -Rational(3, 4) == Rational(-3, 4)

    def test_division_by_zero(self) -> None:
        """除零返回零。/ Division by zero returns zero."""
        assert Rational(5, 1) / Rational(0, 1) == Rational(0)


# ── Rational comparison ─────────────────────────────────────────


class TestRationalComparison:
    """有理数比较测试。"""

    def test_eq(self) -> None:
        """相等。/ Equal."""
        assert Rational(1, 2) == Rational(2, 4)

    def test_lt(self) -> None:
        """小于。/ Less than."""
        assert Rational(1, 3) < Rational(1, 2)

    def test_gt(self) -> None:
        """大于。/ Greater than."""
        assert Rational(2, 3) > Rational(1, 3)

    def test_cmp(self) -> None:
        """全序比较。/ Total comparison."""
        assert Rational(1, 3).cmp(Rational(1, 2)) == Order.LT
        assert Rational(2, 3).cmp(Rational(1, 3)) == Order.GT
        assert Rational(1, 2).cmp(Rational(2, 4)) == Order.EQ


# ── Rational utilities ──────────────────────────────────────────


class TestRationalUtilities:
    """有理数工具测试。"""

    def test_zero_property(self) -> None:
        """零值属性。/ Zero property."""
        assert Rational(5, 1).zero == Rational(0)

    def test_one_property(self) -> None:
        """单位值属性。/ One property."""
        assert Rational(5, 1).one == Rational(1)

    def test_float_value(self) -> None:
        """浮点转换。/ Float conversion."""
        assert abs(Rational(1, 4).float_value - 0.25) < 1e-10

    def test_copy(self) -> None:
        """复制。/ Copy."""
        original = Rational(3, 7)
        copied = original.copy()
        assert copied == original

    def test_repr(self) -> None:
        """字符串表示。/ String representation."""
        assert "Rational" in repr(Rational(3, 4))
