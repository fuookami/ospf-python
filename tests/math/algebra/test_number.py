"""数值类型算术运算测试。

Numeric type arithmetic tests.

测试 Floating、Integer、Rational、UInteger 的
加、减、乘、除及比较操作。
Tests add, sub, mul, div, and comparison for
Floating, Integer, Rational, UInteger.
"""

from __future__ import annotations

from ospf_python.math.algebra.number import (
    Floating,
    Integer,
    Rational,
    UInteger,
)
from ospf_python.utils.functional.ord import Order

# ── UInteger ──────────────────────────────────────────────────────


class TestUInteger:
    """无符号整数测试。"""

    def test_addition(self) -> None:
        """加法。/ Addition."""
        assert UInteger(3) + UInteger(5) == UInteger(8)

    def test_subtraction_clamped(self) -> None:
        """减法截断到零。/ Subtraction clamped to zero."""
        assert UInteger(3) - UInteger(5) == UInteger(0)

    def test_multiplication(self) -> None:
        """乘法。/ Multiplication."""
        assert UInteger(4) * UInteger(5) == UInteger(20)

    def test_division(self) -> None:
        """整数除法。/ Integer division."""
        assert UInteger(10) / UInteger(3) == UInteger(3)

    def test_negation_clamped(self) -> None:
        """取反截断到零。/ Negation clamped to zero."""
        assert -UInteger(5) == UInteger(0)

    def test_zero_value(self) -> None:
        """零值属性。/ Zero property."""
        assert UInteger(5).zero == UInteger(0)

    def test_one_value(self) -> None:
        """单位值属性。/ One property."""
        assert UInteger(5).one == UInteger(1)

    def test_copy(self) -> None:
        """复制。/ Copy."""
        original = UInteger(42)
        copied = original.copy()
        assert copied == original
        assert copied is not original

    def test_negative_input_clamped(self) -> None:
        """负输入截断到零。/ Negative input clamped."""
        assert UInteger(-5) == UInteger(0)

    def test_ordering(self) -> None:
        """排序。/ Ordering."""
        assert UInteger(3) < UInteger(5)
        assert UInteger(5) > UInteger(3)

    def test_repr(self) -> None:
        """字符串表示。/ String representation."""
        assert repr(UInteger(7)) == "UInteger(7)"


# ── Integer ───────────────────────────────────────────────────────


class TestInteger:
    """有符号整数测试。"""

    def test_addition(self) -> None:
        """加法。/ Addition."""
        assert Integer(3) + Integer(-5) == Integer(-2)

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

    def test_cmp_lt(self) -> None:
        """全序比较: 小于。/ Total comparison: LT."""
        assert Integer(3).cmp(Integer(5)) == Order.LT

    def test_cmp_gt(self) -> None:
        """全序比较: 大于。/ Total comparison: GT."""
        assert Integer(5).cmp(Integer(3)) == Order.GT

    def test_cmp_eq(self) -> None:
        """全序比较: 相等。/ Total comparison: EQ."""
        assert Integer(5).cmp(Integer(5)) == Order.EQ

    def test_zero_one(self) -> None:
        """零和单位值。/ Zero and one."""
        assert Integer(5).zero == Integer(0)
        assert Integer(5).one == Integer(1)

    def test_copy(self) -> None:
        """复制。/ Copy."""
        original = Integer(-99)
        copied = original.copy()
        assert copied == original
        assert copied is not original

    def test_repr(self) -> None:
        """字符串表示。/ String representation."""
        assert repr(Integer(-3)) == "Integer(-3)"


# ── Rational ──────────────────────────────────────────────────────


class TestRational:
    """有理数测试。"""

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

    def test_auto_reduce(self) -> None:
        """自动约分。/ Auto reduction."""
        assert Rational(4, 8) == Rational(1, 2)

    def test_negative_denominator(self) -> None:
        """负分母标准化。/ Negative denominator normalized."""
        r = Rational(1, -2)
        assert r.numerator == -1
        assert r.denominator == 2

    def test_zero_denominator(self) -> None:
        """零分母处理。/ Zero denominator handling."""
        r = Rational(5, 0)
        assert r == Rational(0)

    def test_float_value(self) -> None:
        """浮点转换。/ Float conversion."""
        assert abs(Rational(1, 4).float_value - 0.25) < 1e-10

    def test_cmp(self) -> None:
        """全序比较。/ Total comparison."""
        assert Rational(1, 3).cmp(Rational(1, 2)) == Order.LT
        assert Rational(2, 3).cmp(Rational(1, 3)) == Order.GT

    def test_copy(self) -> None:
        """复制。/ Copy."""
        original = Rational(3, 7)
        copied = original.copy()
        assert copied == original

    def test_repr(self) -> None:
        """字符串表示。/ String representation."""
        assert "Rational" in repr(Rational(3, 4))


# ── Floating ──────────────────────────────────────────────────────


class TestFloating:
    """浮点数测试。"""

    def test_addition(self) -> None:
        """加法。/ Addition."""
        assert Floating(1.5) + Floating(2.5) == Floating(4.0)

    def test_subtraction(self) -> None:
        """减法。/ Subtraction."""
        assert Floating(5.0) - Floating(3.0) == Floating(2.0)

    def test_multiplication(self) -> None:
        """乘法。/ Multiplication."""
        assert Floating(2.5) * Floating(4.0) == Floating(10.0)

    def test_division(self) -> None:
        """除法。/ Division."""
        assert Floating(10.0) / Floating(4.0) == Floating(2.5)

    def test_negation(self) -> None:
        """取反。/ Negation."""
        assert -Floating(3.14) == Floating(-3.14)

    def test_cmp(self) -> None:
        """全序比较。/ Total comparison."""
        assert Floating(1.0).cmp(Floating(2.0)) == Order.LT

    def test_constant_providers(self) -> None:
        """常量提供者。/ Constant providers."""
        f = Floating(0.0)
        assert f.zero == Floating(0.0)
        assert f.one == Floating(1.0)
        assert f.two == Floating(2.0)
        assert f.half == Floating(0.5)

    def test_copy(self) -> None:
        """复制。/ Copy."""
        original = Floating(3.14)
        copied = original.copy()
        assert copied == original
        assert copied is not original

    def test_division_by_zero(self) -> None:
        """除零处理。/ Division by zero."""
        assert Floating(5.0) / Floating(0.0) == Floating(0.0)

    def test_repr(self) -> None:
        """字符串表示。/ String representation."""
        assert repr(Floating(2.71)) == "Floating(2.71)"
