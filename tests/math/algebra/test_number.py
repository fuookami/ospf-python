"""Tests for ospf_python.math.algebra.number module."""

from ospf_python.math.algebra.number import Float64, Int64


class TestFloat64:
    """Tests for Float64 type."""

    def test_creation(self) -> None:
        """Test creating Float64."""
        x = Float64(3.14)
        assert x.value == 3.14

    def test_add(self) -> None:
        """Test addition."""
        a = Float64(1.0)
        b = Float64(2.0)
        result = a + b
        assert isinstance(result, Float64)
        assert result.value == 3.0

    def test_sub(self) -> None:
        """Test subtraction."""
        a = Float64(5.0)
        b = Float64(2.0)
        result = a - b
        assert isinstance(result, Float64)
        assert result.value == 3.0

    def test_mul(self) -> None:
        """Test multiplication."""
        a = Float64(3.0)
        b = Float64(4.0)
        result = a * b
        assert isinstance(result, Float64)
        assert result.value == 12.0

    def test_truediv(self) -> None:
        """Test division."""
        a = Float64(10.0)
        b = Float64(2.0)
        result = a / b
        assert isinstance(result, Float64)
        assert result.value == 5.0

    def test_neg(self) -> None:
        """Test negation."""
        a = Float64(3.0)
        result = -a
        assert isinstance(result, Float64)
        assert result.value == -3.0

    def test_abs(self) -> None:
        """Test absolute value."""
        a = Float64(-3.0)
        result = abs(a)
        assert isinstance(result, Float64)
        assert result.value == 3.0

    def test_lt(self) -> None:
        """Test less than."""
        a = Float64(1.0)
        b = Float64(2.0)
        assert a < b
        assert not b < a

    def test_le(self) -> None:
        """Test less than or equal."""
        a = Float64(1.0)
        b = Float64(1.0)
        assert a <= b

    def test_gt(self) -> None:
        """Test greater than."""
        a = Float64(2.0)
        b = Float64(1.0)
        assert a > b

    def test_ge(self) -> None:
        """Test greater than or equal."""
        a = Float64(1.0)
        b = Float64(1.0)
        assert a >= b

    def test_eq(self) -> None:
        """Test equality."""
        a = Float64(1.0)
        b = Float64(1.0)
        assert a == b

    def test_to_float(self) -> None:
        """Test conversion to float."""
        a = Float64(3.14)
        assert a.to_float() == 3.14

    def test_repr(self) -> None:
        """Test repr."""
        a = Float64(3.14)
        assert repr(a) == "Float64(3.14)"


class TestInt64:
    """Tests for Int64 type."""

    def test_creation(self) -> None:
        """Test creating Int64."""
        x = Int64(42)
        assert x.value == 42

    def test_add_int(self) -> None:
        """Test addition with Int64."""
        a = Int64(1)
        b = Int64(2)
        result = a + b
        assert isinstance(result, Int64)
        assert result.value == 3

    def test_add_float(self) -> None:
        """Test addition with Float64."""
        a = Int64(1)
        b = Float64(2.5)
        result = a + b
        assert isinstance(result, Float64)
        assert result.value == 3.5

    def test_sub(self) -> None:
        """Test subtraction."""
        a = Int64(5)
        b = Int64(2)
        result = a - b
        assert isinstance(result, Int64)
        assert result.value == 3

    def test_mul(self) -> None:
        """Test multiplication."""
        a = Int64(3)
        b = Int64(4)
        result = a * b
        assert isinstance(result, Int64)
        assert result.value == 12

    def test_truediv(self) -> None:
        """Test division."""
        a = Int64(10)
        b = Int64(2)
        result = a / b
        assert isinstance(result, Float64)
        assert result.value == 5.0

    def test_neg(self) -> None:
        """Test negation."""
        a = Int64(3)
        result = -a
        assert isinstance(result, Int64)
        assert result.value == -3

    def test_abs(self) -> None:
        """Test absolute value."""
        a = Int64(-3)
        result = abs(a)
        assert isinstance(result, Int64)
        assert result.value == 3

    def test_to_float(self) -> None:
        """Test conversion to float."""
        a = Int64(42)
        assert a.to_float() == 42.0

    def test_repr(self) -> None:
        """Test repr."""
        a = Int64(42)
        assert repr(a) == "Int64(42)"
