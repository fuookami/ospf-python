"""浮点数类型测试。

Floating number type tests.

测试 Floating 类的算术、比较和常量属性。
Tests Floating arithmetic, comparison, and constant properties.
"""

from __future__ import annotations

import math

from ospf_python.math.algebra.number.floating import Floating
from ospf_python.utils.functional.ord import Order

# ── Floating creation ───────────────────────────────────────────


class TestFloatingCreation:
    """浮点数创建测试。"""

    def test_basic_creation(self) -> None:
        """基本创建。/ Basic creation."""
        f = Floating(3.14)
        assert f.value == 3.14

    def test_zero_creation(self) -> None:
        """零值创建。/ Zero creation."""
        f = Floating(0.0)
        assert f.value == 0.0

    def test_negative_creation(self) -> None:
        """负值创建。/ Negative creation."""
        f = Floating(-2.5)
        assert f.value == -2.5


# ── Floating arithmetic ────────────────────────────────────────


class TestFloatingArithmetic:
    """浮点数算术测试。"""

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

    def test_division_by_zero(self) -> None:
        """除零返回零。/ Division by zero returns zero."""
        assert Floating(5.0) / Floating(0.0) == Floating(0.0)


# ── Floating comparison ─────────────────────────────────────────


class TestFloatingComparison:
    """浮点数比较测试。"""

    def test_eq(self) -> None:
        """相等。/ Equal."""
        assert Floating(1.0) == Floating(1.0)

    def test_ne(self) -> None:
        """不等。/ Not equal."""
        assert Floating(1.0) != Floating(2.0)

    def test_lt(self) -> None:
        """小于。/ Less than."""
        assert Floating(1.0) < Floating(2.0)

    def test_le(self) -> None:
        """小于等于。/ Less or equal."""
        assert Floating(1.0) <= Floating(1.0)

    def test_gt(self) -> None:
        """大于。/ Greater than."""
        assert Floating(2.0) > Floating(1.0)

    def test_ge(self) -> None:
        """大于等于。/ Greater or equal."""
        assert Floating(2.0) >= Floating(2.0)

    def test_cmp_lt(self) -> None:
        """全序比较 LT。/ Total comparison LT."""
        assert Floating(1.0).cmp(Floating(2.0)) == Order.LT

    def test_cmp_gt(self) -> None:
        """全序比较 GT。/ Total comparison GT."""
        assert Floating(2.0).cmp(Floating(1.0)) == Order.GT

    def test_cmp_eq(self) -> None:
        """全序比较 EQ。/ Total comparison EQ."""
        assert Floating(1.0).cmp(Floating(1.0)) == Order.EQ


# ── Floating constants ──────────────────────────────────────────


class TestFloatingConstants:
    """浮点数常量测试。"""

    def test_zero(self) -> None:
        """零值。/ Zero."""
        assert Floating(0.0).zero == Floating(0.0)

    def test_one(self) -> None:
        """单位值。/ One."""
        assert Floating(0.0).one == Floating(1.0)

    def test_two(self) -> None:
        """二值。/ Two."""
        assert Floating(0.0).two == Floating(2.0)

    def test_half(self) -> None:
        """半值。/ Half."""
        assert Floating(0.0).half == Floating(0.5)

    def test_positive_inf(self) -> None:
        """正无穷。/ Positive infinity."""
        assert Floating(0.0).positive_inf == Floating(math.inf)

    def test_negative_inf(self) -> None:
        """负无穷。/ Negative infinity."""
        assert Floating(0.0).negative_inf == Floating(-math.inf)


# ── Floating utilities ──────────────────────────────────────────


class TestFloatingUtilities:
    """浮点数工具测试。"""

    def test_copy(self) -> None:
        """复制。/ Copy."""
        original = Floating(3.14)
        copied = original.copy()
        assert copied == original
        assert copied is not original

    def test_hash(self) -> None:
        """哈希。/ Hash."""
        a = Floating(3.14)
        b = Floating(3.14)
        assert hash(a) == hash(b)

    def test_repr(self) -> None:
        """字符串表示。/ String representation."""
        assert repr(Floating(2.71)) == "Floating(2.71)"
