"""NumericInteger 和 NumericUInteger 测试。

Tests for NumericInteger and NumericUInteger classes
covering construction, arithmetic, comparison, and
overflow handling.
"""

from __future__ import annotations

import pytest

from ospf_python.math.algebra.number.numeric_integer import NumericInteger
from ospf_python.math.algebra.number.numeric_u_integer import (
    NumericUInteger,
)

# ============================================================
# NumericInteger
# ============================================================


class TestNumericIntegerConstruction:
    """NumericInteger 构造测试。/ Construction tests."""

    def test_default_value(self) -> None:
        """默认值为 0。/ Default value is 0."""
        n = NumericInteger()
        assert n.value == 0

    def test_positive_value(self) -> None:
        """正整数值。/ Positive integer value."""
        n = NumericInteger(42)
        assert n.value == 42

    def test_negative_value(self) -> None:
        """负整数值。/ Negative integer value."""
        n = NumericInteger(-100)
        assert n.value == -100

    def test_clamp_to_max(self) -> None:
        """超过最大值时钳制。/ Clamp to MAX_VALUE."""
        n = NumericInteger(NumericInteger.MAX_VALUE + 100)
        assert n.value == NumericInteger.MAX_VALUE

    def test_clamp_to_min(self) -> None:
        """低于最小值时钳制。/ Clamp to MIN_VALUE."""
        n = NumericInteger(NumericInteger.MIN_VALUE - 100)
        assert n.value == NumericInteger.MIN_VALUE

    def test_max_boundary(self) -> None:
        """恰好在最大边界。/ Exactly at MAX boundary."""
        n = NumericInteger(NumericInteger.MAX_VALUE)
        assert n.value == NumericInteger.MAX_VALUE

    def test_min_boundary(self) -> None:
        """恰好在最小边界。/ Exactly at MIN boundary."""
        n = NumericInteger(NumericInteger.MIN_VALUE)
        assert n.value == NumericInteger.MIN_VALUE

    def test_frozen(self) -> None:
        """frozen dataclass。/ frozen dataclass."""
        n = NumericInteger(5)
        with pytest.raises(AttributeError):
            n._value = 10  # type: ignore[misc]


class TestNumericIntegerSafeAdd:
    """safe_add 测试。/ Safe addition tests."""

    def test_add_two_integers(self) -> None:
        """两个 NumericInteger 相加。/ Add two NumericIntegers."""
        a = NumericInteger(10)
        b = NumericInteger(20)
        result = a.safe_add(b)
        assert result.value == 30

    def test_add_with_int(self) -> None:
        """NumericInteger + int。/ NumericInteger + int."""
        a = NumericInteger(10)
        result = a.safe_add(5)
        assert result.value == 15

    def test_add_negative(self) -> None:
        """加上负数。/ Add negative number."""
        a = NumericInteger(10)
        result = a.safe_add(-3)
        assert result.value == 7

    def test_add_overflow_clamp(self) -> None:
        """加法溢出钳制。/ Addition overflow clamps."""
        a = NumericInteger(NumericInteger.MAX_VALUE)
        result = a.safe_add(100)
        assert result.value == NumericInteger.MAX_VALUE

    def test_add_underflow_clamp(self) -> None:
        """加法下溢钳制。/ Addition underflow clamps."""
        a = NumericInteger(NumericInteger.MIN_VALUE)
        result = a.safe_add(-100)
        assert result.value == NumericInteger.MIN_VALUE


class TestNumericIntegerSafeMul:
    """safe_mul 测试。/ Safe multiplication tests."""

    def test_mul_two_integers(self) -> None:
        """两个 NumericInteger 相乘。/ Multiply two NumericIntegers."""
        a = NumericInteger(6)
        b = NumericInteger(7)
        result = a.safe_mul(b)
        assert result.value == 42

    def test_mul_with_int(self) -> None:
        """NumericInteger * int。/ NumericInteger * int."""
        a = NumericInteger(6)
        result = a.safe_mul(7)
        assert result.value == 42

    def test_mul_by_zero(self) -> None:
        """乘以零。/ Multiply by zero."""
        a = NumericInteger(100)
        result = a.safe_mul(0)
        assert result.value == 0

    def test_mul_overflow_clamp(self) -> None:
        """乘法溢出钳制。/ Multiplication overflow clamps."""
        a = NumericInteger(NumericInteger.MAX_VALUE)
        result = a.safe_mul(2)
        assert result.value == NumericInteger.MAX_VALUE

    def test_mul_underflow_clamp(self) -> None:
        """乘法下溢钳制。/ Multiplication underflow clamps."""
        a = NumericInteger(NumericInteger.MIN_VALUE)
        result = a.safe_mul(2)
        assert result.value == NumericInteger.MIN_VALUE


class TestNumericIntegerComparison:
    """比较运算测试。/ Comparison tests."""

    def test_eq_same(self) -> None:
        """相等比较。/ Equality."""
        assert NumericInteger(5) == NumericInteger(5)

    def test_eq_different(self) -> None:
        """不等比较。/ Inequality."""
        assert NumericInteger(5) != NumericInteger(6)

    def test_eq_with_int(self) -> None:
        """与 int 比较。/ Compare with int."""
        assert NumericInteger(5) == 5

    def test_eq_not_implemented(self) -> None:
        """与不支持类型比较返回 NotImplemented。/ NotImplemented for str."""
        assert NumericInteger(5).__eq__("five") is NotImplemented

    def test_lt(self) -> None:
        """小于。/ Less than."""
        assert NumericInteger(3) < NumericInteger(5)

    def test_lt_with_int(self) -> None:
        """小于 int。/ Less than int."""
        assert NumericInteger(3) < 5

    def test_le(self) -> None:
        """小于等于。/ Less or equal."""
        assert NumericInteger(5) <= NumericInteger(5)
        assert NumericInteger(3) <= NumericInteger(5)

    def test_gt(self) -> None:
        """大于。/ Greater than."""
        assert NumericInteger(5) > NumericInteger(3)

    def test_ge(self) -> None:
        """大于等于。/ Greater or equal."""
        assert NumericInteger(5) >= NumericInteger(5)
        assert NumericInteger(5) >= NumericInteger(3)


class TestNumericIntegerHash:
    """哈希和字符串测试。/ Hash and string tests."""

    def test_hash(self) -> None:
        """哈希值一致。/ Hash consistency."""
        a = NumericInteger(42)
        b = NumericInteger(42)
        assert hash(a) == hash(b)

    def test_str(self) -> None:
        """字符串表示。/ String representation."""
        assert str(NumericInteger(42)) == "42"

    def test_repr(self) -> None:
        """开发者表示。/ Developer representation."""
        assert repr(NumericInteger(42)) == "NumericInteger(42)"


# ============================================================
# NumericUInteger
# ============================================================


class TestNumericUIntegerConstruction:
    """NumericUInteger 构造测试。/ Construction tests."""

    def test_positive_value(self) -> None:
        """正整数值。/ Positive integer value."""
        n = NumericUInteger(42)
        assert n.value == 42

    def test_zero(self) -> None:
        """零值。/ Zero value."""
        n = NumericUInteger(0)
        assert n.value == 0

    def test_negative_raises(self) -> None:
        """负值抛出 ValueError。/ Negative raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            NumericUInteger(-1)

    def test_frozen(self) -> None:
        """frozen dataclass。/ frozen dataclass."""
        n = NumericUInteger(5)
        with pytest.raises(AttributeError):
            n._value = 10  # type: ignore[misc]


class TestNumericUIntegerArithmetic:
    """算术运算测试。/ Arithmetic tests."""

    def test_safe_add(self) -> None:
        """安全加法。/ Safe addition."""
        a = NumericUInteger(10)
        b = NumericUInteger(20)
        result = a.safe_add(b)
        assert result.value == 30

    def test_safe_mul(self) -> None:
        """安全乘法。/ Safe multiplication."""
        a = NumericUInteger(6)
        b = NumericUInteger(7)
        result = a.safe_mul(b)
        assert result.value == 42

    def test_add_operator(self) -> None:
        """加法运算符。/ Addition operator."""
        result = NumericUInteger(10) + NumericUInteger(20)
        assert result.value == 30

    def test_mul_operator(self) -> None:
        """乘法运算符。/ Multiplication operator."""
        result = NumericUInteger(6) * NumericUInteger(7)
        assert result.value == 42


class TestNumericUIntegerComparison:
    """比较运算测试。/ Comparison tests."""

    def test_eq(self) -> None:
        """相等比较。/ Equality."""
        assert NumericUInteger(5) == NumericUInteger(5)

    def test_neq(self) -> None:
        """不等比较。/ Inequality."""
        assert NumericUInteger(5) != NumericUInteger(6)

    def test_eq_not_implemented(self) -> None:
        """与不支持类型比较返回 NotImplemented。/ NotImplemented."""
        assert NumericUInteger(5).__eq__("five") is NotImplemented

    def test_lt(self) -> None:
        """小于。/ Less than."""
        assert NumericUInteger(3) < NumericUInteger(5)

    def test_le(self) -> None:
        """小于等于。/ Less or equal."""
        assert NumericUInteger(5) <= NumericUInteger(5)

    def test_hash(self) -> None:
        """哈希值一致。/ Hash consistency."""
        assert hash(NumericUInteger(42)) == hash(NumericUInteger(42))

    def test_str(self) -> None:
        """字符串表示。/ String representation."""
        assert str(NumericUInteger(42)) == "42"
