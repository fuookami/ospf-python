"""Tests for ospf_python.math.symbol.expression module."""

from ospf_python.math.symbol.expression import (
    AddExpr,
    Constant,
    DivExpr,
    FunctionExpr,
    MulExpr,
    NegExpr,
    PowExpr,
    SubExpr,
    Variable,
    const,
    cos,
    exp,
    func,
    log,
    sin,
    sqrt,
    var,
)


class TestConstant:
    """Tests for Constant."""

    def test_creation(self) -> None:
        """Test creating constant."""
        c = Constant(5.0)
        assert c.value == 5.0

    def test_evaluate(self) -> None:
        """Test evaluating constant."""
        c = Constant(5.0)
        assert c.evaluate({}) == 5.0

    def test_repr(self) -> None:
        """Test string representation."""
        c = Constant(5.0)
        assert repr(c) == "5.0"

    def test_to_dict(self) -> None:
        """Test serialization."""
        c = Constant(5.0)
        d = c.to_dict()
        assert d == {"type": "Constant", "value": 5.0}


class TestVariable:
    """Tests for Variable."""

    def test_creation(self) -> None:
        """Test creating variable."""
        v = Variable("x")
        assert v.name == "x"

    def test_evaluate(self) -> None:
        """Test evaluating variable."""
        v = Variable("x")
        assert v.evaluate({"x": 3.0}) == 3.0

    def test_repr(self) -> None:
        """Test string representation."""
        v = Variable("x")
        assert repr(v) == "x"

    def test_to_dict(self) -> None:
        """Test serialization."""
        v = Variable("x")
        d = v.to_dict()
        assert d == {"type": "Variable", "name": "x"}


class TestAddExpr:
    """Tests for AddExpr."""

    def test_creation(self) -> None:
        """Test creating addition."""
        expr = Constant(1.0) + Constant(2.0)
        assert isinstance(expr, AddExpr)

    def test_evaluate(self) -> None:
        """Test evaluating addition."""
        expr = Constant(1.0) + Constant(2.0)
        assert expr.evaluate({}) == 3.0

    def test_repr(self) -> None:
        """Test string representation."""
        expr = Constant(1.0) + Constant(2.0)
        assert "+" in repr(expr)

    def test_to_dict(self) -> None:
        """Test serialization."""
        expr = Constant(1.0) + Constant(2.0)
        d = expr.to_dict()
        assert d["type"] == "Add"


class TestSubExpr:
    """Tests for SubExpr."""

    def test_creation(self) -> None:
        """Test creating subtraction."""
        expr = Constant(5.0) - Constant(2.0)
        assert isinstance(expr, SubExpr)

    def test_evaluate(self) -> None:
        """Test evaluating subtraction."""
        expr = Constant(5.0) - Constant(2.0)
        assert expr.evaluate({}) == 3.0


class TestMulExpr:
    """Tests for MulExpr."""

    def test_creation(self) -> None:
        """Test creating multiplication."""
        expr = Constant(3.0) * Constant(4.0)
        assert isinstance(expr, MulExpr)

    def test_evaluate(self) -> None:
        """Test evaluating multiplication."""
        expr = Constant(3.0) * Constant(4.0)
        assert expr.evaluate({}) == 12.0


class TestDivExpr:
    """Tests for DivExpr."""

    def test_creation(self) -> None:
        """Test creating division."""
        expr = Constant(10.0) / Constant(2.0)
        assert isinstance(expr, DivExpr)

    def test_evaluate(self) -> None:
        """Test evaluating division."""
        expr = Constant(10.0) / Constant(2.0)
        assert expr.evaluate({}) == 5.0


class TestPowExpr:
    """Tests for PowExpr."""

    def test_creation(self) -> None:
        """Test creating power."""
        expr = Constant(2.0) ** Constant(3.0)
        assert isinstance(expr, PowExpr)

    def test_evaluate(self) -> None:
        """Test evaluating power."""
        expr = Constant(2.0) ** Constant(3.0)
        assert expr.evaluate({}) == 8.0


class TestNegExpr:
    """Tests for NegExpr."""

    def test_creation(self) -> None:
        """Test creating negation."""
        expr = -Constant(5.0)
        assert isinstance(expr, NegExpr)

    def test_evaluate(self) -> None:
        """Test evaluating negation."""
        expr = -Constant(5.0)
        assert expr.evaluate({}) == -5.0


class TestFunctionExpr:
    """Tests for FunctionExpr."""

    def test_creation(self) -> None:
        """Test creating function."""
        expr = sin(Constant(0.0))
        assert isinstance(expr, FunctionExpr)
        assert expr.name == "sin"

    def test_evaluate(self) -> None:
        """Test evaluating function."""

        expr = sin(Constant(0.0))
        assert expr.evaluate({}) == 0.0

        expr = cos(Constant(0.0))
        assert expr.evaluate({}) == 1.0

    def test_repr(self) -> None:
        """Test string representation."""
        expr = sin(Variable("x"))
        assert "sin" in repr(expr)


class TestOperatorOverloading:
    """Tests for operator overloading."""

    def test_complex_expression(self) -> None:
        """Test complex expression."""
        # x^2 + 2*x + 1
        x = Variable("x")
        expr = x**2 + 2 * x + 1
        assert expr.evaluate({"x": 3.0}) == 16.0  # 9 + 6 + 1

    def test_radd(self) -> None:
        """Test reverse add."""
        x = Variable("x")
        expr = 2 + x
        assert expr.evaluate({"x": 3.0}) == 5.0

    def test_rsub(self) -> None:
        """Test reverse subtract."""
        x = Variable("x")
        expr = 10 - x
        assert expr.evaluate({"x": 3.0}) == 7.0

    def test_rmul(self) -> None:
        """Test reverse multiply."""
        x = Variable("x")
        expr = 2 * x
        assert expr.evaluate({"x": 3.0}) == 6.0

    def test_rtruediv(self) -> None:
        """Test reverse divide."""
        x = Variable("x")
        expr = 10 / x
        assert expr.evaluate({"x": 2.0}) == 5.0

    def test_rpow(self) -> None:
        """Test reverse power."""
        x = Variable("x")
        expr = 2**x
        assert expr.evaluate({"x": 3.0}) == 8.0


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_var(self) -> None:
        """Test var factory."""
        v = var("x")
        assert isinstance(v, Variable)
        assert v.name == "x"

    def test_const(self) -> None:
        """Test const factory."""
        c = const(5.0)
        assert isinstance(c, Constant)
        assert c.value == 5.0

    def test_func(self) -> None:
        """Test func factory."""
        f = func("sin", const(0.0))
        assert isinstance(f, FunctionExpr)
        assert f.name == "sin"

    def test_sin(self) -> None:
        """Test sin factory."""
        s = sin(const(0.0))
        assert s.evaluate({}) == 0.0

    def test_cos(self) -> None:
        """Test cos factory."""
        c = cos(const(0.0))
        assert c.evaluate({}) == 1.0

    def test_exp(self) -> None:
        """Test exp factory."""
        e = exp(const(0.0))
        assert e.evaluate({}) == 1.0

    def test_log(self) -> None:
        """Test log factory."""
        log_expr = log(const(1.0))
        assert log_expr.evaluate({}) == 0.0

    def test_sqrt(self) -> None:
        """Test sqrt factory."""
        s = sqrt(const(4.0))
        assert s.evaluate({}) == 2.0


class TestSerde:
    """Tests for serialization/deserialization."""

    def test_constant_serde(self) -> None:
        """Test constant serde."""
        c = Constant(5.0)
        d = c.to_dict()
        assert d == {"type": "Constant", "value": 5.0}

    def test_variable_serde(self) -> None:
        """Test variable serde."""
        v = Variable("x")
        d = v.to_dict()
        assert d == {"type": "Variable", "name": "x"}

    def test_add_serde(self) -> None:
        """Test add serde."""
        expr = Constant(1.0) + Constant(2.0)
        d = expr.to_dict()
        assert d["type"] == "Add"


class TestDSLUsage:
    """Tests for DSL usage patterns."""

    def test_quadratic_formula(self) -> None:
        """Test quadratic formula DSL."""
        # x^2 - 4*x + 4 = (x-2)^2
        x = var("x")
        expr = x**2 - 4 * x + 4
        assert expr.evaluate({"x": 2.0}) == 0.0
        assert expr.evaluate({"x": 3.0}) == 1.0

    def test_trigonometric(self) -> None:
        """Test trigonometric DSL."""

        # sin^2(x) + cos^2(x) = 1
        x = var("x")
        expr = sin(x) ** 2 + cos(x) ** 2
        assert abs(expr.evaluate({"x": 0.5}) - 1.0) < 1e-10
        assert abs(expr.evaluate({"x": 1.0}) - 1.0) < 1e-10
