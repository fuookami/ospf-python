"""Tests for ospf_python.core.symbol module."""

from ospf_python.core.symbol import (
    AddSymbol,
    ConstantSymbol,
    DivSymbol,
    LinearExpression,
    LinearTerm,
    MulSymbol,
    NegSymbol,
    SubSymbol,
    VariableSymbol,
    const,
    flatten,
    linear_expr,
    linear_term,
    var,
)
from ospf_python.core.token import TokenType


class TestVariableSymbol:
    """Tests for VariableSymbol."""

    def test_creation(self) -> None:
        """Test creating variable symbol."""
        v = VariableSymbol("x")
        assert v.name == "x"

    def test_evaluate(self) -> None:
        """Test evaluating variable."""
        v = VariableSymbol("x")
        assert v.evaluate({"x": 5.0}) == 5.0

    def test_flatten(self) -> None:
        """Test flattening variable."""
        v = VariableSymbol("x")
        tokens = v.flatten()
        assert len(tokens) == 1
        assert tokens[0].name == "x"
        assert tokens[0].token_type == TokenType.VARIABLE

    def test_repr(self) -> None:
        """Test string representation."""
        v = VariableSymbol("x")
        assert repr(v) == "x"


class TestConstantSymbol:
    """Tests for ConstantSymbol."""

    def test_creation(self) -> None:
        """Test creating constant symbol."""
        c = ConstantSymbol(5.0)
        assert c.value == 5.0

    def test_evaluate(self) -> None:
        """Test evaluating constant."""
        c = ConstantSymbol(5.0)
        assert c.evaluate({}) == 5.0

    def test_flatten(self) -> None:
        """Test flattening constant."""
        c = ConstantSymbol(5.0)
        tokens = c.flatten()
        assert len(tokens) == 0

    def test_repr(self) -> None:
        """Test string representation."""
        c = ConstantSymbol(5.0)
        assert repr(c) == "5.0"


class TestAddSymbol:
    """Tests for AddSymbol."""

    def test_creation(self) -> None:
        """Test creating addition."""
        expr = VariableSymbol("x") + ConstantSymbol(1.0)
        assert isinstance(expr, AddSymbol)

    def test_evaluate(self) -> None:
        """Test evaluating addition."""
        expr = VariableSymbol("x") + ConstantSymbol(1.0)
        assert expr.evaluate({"x": 5.0}) == 6.0

    def test_flatten(self) -> None:
        """Test flattening addition."""
        expr = VariableSymbol("x") + VariableSymbol("y")
        tokens = expr.flatten()
        assert len(tokens) == 2


class TestMulSymbol:
    """Tests for MulSymbol."""

    def test_creation(self) -> None:
        """Test creating multiplication."""
        expr = VariableSymbol("x") * ConstantSymbol(2.0)
        assert isinstance(expr, MulSymbol)

    def test_evaluate(self) -> None:
        """Test evaluating multiplication."""
        expr = VariableSymbol("x") * ConstantSymbol(2.0)
        assert expr.evaluate({"x": 5.0}) == 10.0


class TestSubSymbol:
    """Tests for SubSymbol."""

    def test_creation(self) -> None:
        """Test creating subtraction."""
        expr = VariableSymbol("x") - ConstantSymbol(1.0)
        assert isinstance(expr, SubSymbol)

    def test_evaluate(self) -> None:
        """Test evaluating subtraction."""
        expr = VariableSymbol("x") - ConstantSymbol(1.0)
        assert expr.evaluate({"x": 5.0}) == 4.0


class TestDivSymbol:
    """Tests for DivSymbol."""

    def test_creation(self) -> None:
        """Test creating division."""
        expr = VariableSymbol("x") / ConstantSymbol(2.0)
        assert isinstance(expr, DivSymbol)

    def test_evaluate(self) -> None:
        """Test evaluating division."""
        expr = VariableSymbol("x") / ConstantSymbol(2.0)
        assert expr.evaluate({"x": 6.0}) == 3.0


class TestNegSymbol:
    """Tests for NegSymbol."""

    def test_creation(self) -> None:
        """Test creating negation."""
        expr = -VariableSymbol("x")
        assert isinstance(expr, NegSymbol)

    def test_evaluate(self) -> None:
        """Test evaluating negation."""
        expr = -VariableSymbol("x")
        assert expr.evaluate({"x": 5.0}) == -5.0


class TestLinearTerm:
    """Tests for LinearTerm."""

    def test_creation(self) -> None:
        """Test creating linear term."""
        t = LinearTerm(2.0, "x")
        assert t.coefficient == 2.0
        assert t.variable == "x"

    def test_evaluate(self) -> None:
        """Test evaluating linear term."""
        t = LinearTerm(2.0, "x")
        assert t.evaluate({"x": 3.0}) == 6.0

    def test_flatten(self) -> None:
        """Test flattening linear term."""
        t = LinearTerm(2.0, "x")
        tokens = t.flatten()
        assert len(tokens) == 1
        assert tokens[0].name == "x"

    def test_repr(self) -> None:
        """Test string representation."""
        t = LinearTerm(2.0, "x")
        assert "2.0" in repr(t)
        assert "x" in repr(t)


class TestLinearExpression:
    """Tests for LinearExpression."""

    def test_creation(self) -> None:
        """Test creating linear expression."""
        terms = [LinearTerm(2.0, "x"), LinearTerm(3.0, "y")]
        expr = LinearExpression(tuple(terms), 5.0)
        assert len(expr.terms) == 2
        assert expr.constant == 5.0

    def test_evaluate(self) -> None:
        """Test evaluating linear expression."""
        terms = [LinearTerm(2.0, "x"), LinearTerm(3.0, "y")]
        expr = LinearExpression(tuple(terms), 5.0)
        assert expr.evaluate({"x": 1.0, "y": 2.0}) == 13.0  # 2*1 + 3*2 + 5

    def test_flatten(self) -> None:
        """Test flattening linear expression."""
        terms = [LinearTerm(2.0, "x"), LinearTerm(3.0, "y")]
        expr = LinearExpression(tuple(terms), 5.0)
        tokens = expr.flatten()
        assert len(tokens) == 2


class TestFlatten:
    """Tests for flatten function."""

    def test_flatten_simple(self) -> None:
        """Test flattening simple expression."""
        expr = VariableSymbol("x") + VariableSymbol("y")
        tokens = flatten(expr)
        assert len(tokens) == 2
        assert tokens[0].name == "x"
        assert tokens[1].name == "y"

    def test_flatten_nested(self) -> None:
        """Test flattening nested expression."""
        # (x + y) * z
        expr = (VariableSymbol("x") + VariableSymbol("y")) * VariableSymbol("z")
        tokens = flatten(expr)
        assert len(tokens) == 3
        names = [t.name for t in tokens]
        assert "x" in names
        assert "y" in names
        assert "z" in names


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_var(self) -> None:
        """Test var factory."""
        v = var("x")
        assert isinstance(v, VariableSymbol)

    def test_const(self) -> None:
        """Test const factory."""
        c = const(5.0)
        assert isinstance(c, ConstantSymbol)

    def test_linear_term(self) -> None:
        """Test linear_term factory."""
        t = linear_term(2.0, "x")
        assert isinstance(t, LinearTerm)

    def test_linear_expr(self) -> None:
        """Test linear_expr factory."""
        terms = [linear_term(2.0, "x"), linear_term(3.0, "y")]
        expr = linear_expr(terms, 5.0)
        assert isinstance(expr, LinearExpression)
