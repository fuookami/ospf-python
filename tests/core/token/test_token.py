"""Tests for ospf_python.core.token module."""

from ospf_python.core.token import (
    ConstraintToken,
    ObjectiveToken,
    Token,
    TokenType,
    VariableToken,
    constraint_token,
    objective_token,
    variable_token,
)


class TestToken:
    """Tests for Token."""

    def test_creation(self) -> None:
        """Test creating token."""
        t = Token("x", TokenType.VARIABLE)
        assert t.name == "x"
        assert t.token_type == TokenType.VARIABLE

    def test_with_index(self) -> None:
        """Test token with index."""
        t = Token("x", TokenType.VARIABLE, index=5)
        assert t.index == 5

    def test_repr(self) -> None:
        """Test string representation."""
        t = Token("x", TokenType.VARIABLE, index=5)
        assert "x" in repr(t)
        assert "variable" in repr(t)


class TestVariableToken:
    """Tests for VariableToken."""

    def test_creation(self) -> None:
        """Test creating variable token."""
        t = VariableToken("x")
        assert t.token_type == TokenType.VARIABLE


class TestConstraintToken:
    """Tests for ConstraintToken."""

    def test_creation(self) -> None:
        """Test creating constraint token."""
        t = ConstraintToken("c1")
        assert t.token_type == TokenType.CONSTRAINT


class TestObjectiveToken:
    """Tests for ObjectiveToken."""

    def test_creation(self) -> None:
        """Test creating objective token."""
        t = ObjectiveToken("obj")
        assert t.token_type == TokenType.OBJECTIVE


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_variable_token(self) -> None:
        """Test variable token factory."""
        t = variable_token("x", 5)
        assert isinstance(t, VariableToken)
        assert t.index == 5

    def test_constraint_token(self) -> None:
        """Test constraint token factory."""
        t = constraint_token("c1", 0)
        assert isinstance(t, ConstraintToken)

    def test_objective_token(self) -> None:
        """Test objective token factory."""
        t = objective_token("obj")
        assert isinstance(t, ObjectiveToken)
