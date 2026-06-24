"""无符号整数类型测试。

Unsigned integer type tests.

测试 UInteger 类的算术、比较和截断行为。
Tests UInteger arithmetic, comparison, and clamping behavior.
"""

from __future__ import annotations

from ospf_python.math.algebra.number.uinteger import UInteger

# ── UInteger creation ───────────────────────────────────────────


class TestUIntegerCreation:
    """无符号整数创建测试。"""

    def test_basic_creation(self) -> None:
        """基本创建。/ Basic creation."""
        u = UInteger(42)
        assert u.value == 42

    def test_zero_creation(self) -> None:
        """零值创建。/ Zero creation."""
        u = UInteger(0)
        assert u.value == 0

    def test_negative_clamped(self) -> None:
        """负输入截断到零。/ Negative input clamped."""
        assert UInteger(-5) == UInteger(0)


# ── UInteger arithmetic ─────────────────────────────────────────


class TestUIntegerArithmetic:
    """无符号整数算术测试。"""

    def test_addition(self) -> None:
        """加法。/ Addition."""
        assert UInteger(3) + UInteger(5) == UInteger(8)

    def test_subtraction_clamped(self) -> None:
        """减法截断到零。/ Subtraction clamped."""
        assert UInteger(3) - UInteger(5) == UInteger(0)

    def test_subtraction_normal(self) -> None:
        """正常减法。/ Normal subtraction."""
        assert UInteger(10) - UInteger(3) == UInteger(7)

    def test_multiplication(self) -> None:
        """乘法。/ Multiplication."""
        assert UInteger(4) * UInteger(5) == UInteger(20)

    def test_division(self) -> None:
        """整数除法。/ Integer division."""
        assert UInteger(10) / UInteger(3) == UInteger(3)

    def test_negation_clamped(self) -> None:
        """取反截断到零。/ Negation clamped."""
        assert -UInteger(5) == UInteger(0)

    def test_division_by_zero(self) -> None:
        """除零返回零。/ Division by zero returns zero."""
        assert UInteger(5) / UInteger(0) == UInteger(0)


# ── UInteger comparison ─────────────────────────────────────────


class TestUIntegerComparison:
    """无符号整数比较测试。"""

    def test_eq(self) -> None:
        """相等。/ Equal."""
        assert UInteger(5) == UInteger(5)

    def test_ne(self) -> None:
        """不等。/ Not equal."""
        assert UInteger(5) != UInteger(3)

    def test_ordering(self) -> None:
        """排序。/ Ordering."""
        assert UInteger(3) < UInteger(5)
        assert UInteger(5) > UInteger(3)


# ── UInteger utilities ──────────────────────────────────────────


class TestUIntegerUtilities:
    """无符号整数工具测试。"""

    def test_zero_property(self) -> None:
        """零值属性。/ Zero property."""
        assert UInteger(5).zero == UInteger(0)

    def test_one_property(self) -> None:
        """单位值属性。/ One property."""
        assert UInteger(5).one == UInteger(1)

    def test_copy(self) -> None:
        """复制。/ Copy."""
        original = UInteger(42)
        copied = original.copy()
        assert copied == original
        assert copied is not original

    def test_repr(self) -> None:
        """字符串表示。/ String representation."""
        assert repr(UInteger(7)) == "UInteger(7)"
