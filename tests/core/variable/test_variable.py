"""Tests for ospf_python.core.variable module."""

from ospf_python.core.variable import (
    BinaryVariable,
    IntegerVariable,
    LinearVariable,
    Variable,
    VariableType,
    binary,
    continuous,
    integer,
)


class TestVariable:
    """Tests for Variable."""

    def test_creation(self) -> None:
        """Test creating variable."""
        v = Variable("x")
        assert v.name == "x"
        assert v.variable_type == VariableType.CONTINUOUS

    def test_with_bounds(self) -> None:
        """Test variable with bounds."""
        v = Variable("x", lower_bound=0.0, upper_bound=10.0)
        assert v.lower_bound == 0.0
        assert v.upper_bound == 10.0

    def test_repr(self) -> None:
        """Test string representation."""
        v = Variable("x", lower_bound=0.0, upper_bound=10.0)
        assert "x" in repr(v)
        assert "continuous" in repr(v)


class TestLinearVariable:
    """Tests for LinearVariable."""

    def test_creation(self) -> None:
        """Test creating linear variable."""
        v = LinearVariable("x", coefficient=2.0)
        assert v.name == "x"
        assert v.coefficient == 2.0

    def test_repr(self) -> None:
        """Test string representation."""
        v = LinearVariable("x", coefficient=2.0)
        assert "2.0" in repr(v)
        assert "x" in repr(v)


class TestIntegerVariable:
    """Tests for IntegerVariable."""

    def test_creation(self) -> None:
        """Test creating integer variable."""
        v = IntegerVariable("x")
        assert v.variable_type == VariableType.INTEGER


class TestBinaryVariable:
    """Tests for BinaryVariable."""

    def test_creation(self) -> None:
        """Test creating binary variable."""
        v = BinaryVariable("x")
        assert v.variable_type == VariableType.BINARY
        assert v.lower_bound == 0.0
        assert v.upper_bound == 1.0


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_continuous(self) -> None:
        """Test continuous factory."""
        v = continuous("x", 0.0, 10.0)
        assert isinstance(v, Variable)
        assert v.variable_type == VariableType.CONTINUOUS

    def test_integer(self) -> None:
        """Test integer factory."""
        v = integer("x", 0, 10)
        assert isinstance(v, IntegerVariable)

    def test_binary(self) -> None:
        """Test binary factory."""
        v = binary("x")
        assert isinstance(v, BinaryVariable)
