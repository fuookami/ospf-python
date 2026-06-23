"""Tests for ospf_python.math.symbol module."""

from ospf_python.math.symbol import (
    Inequality,
    Monomial,
    Polynomial,
    constant,
    variable,
)


class TestMonomial:
    """Tests for Monomial."""

    def test_creation(self) -> None:
        """Test creating monomial."""
        m = Monomial(2.0, (("x", 1), ("y", 2)))
        assert m.coefficient == 2.0
        assert m.variables == (("x", 1), ("y", 2))

    def test_evaluate(self) -> None:
        """Test evaluating monomial."""
        m = Monomial(2.0, (("x", 1), ("y", 2)))
        result = m.evaluate({"x": 3.0, "y": 4.0})
        assert result == 2.0 * 3.0 * 4.0**2

    def test_degree(self) -> None:
        """Test monomial degree."""
        m = Monomial(2.0, (("x", 1), ("y", 2)))
        assert m.degree() == 3

    def test_add_like_terms(self) -> None:
        """Test adding like terms."""
        m1 = Monomial(2.0, (("x", 1),))
        m2 = Monomial(3.0, (("x", 1),))
        result = m1 + m2
        assert isinstance(result, Polynomial)
        assert len(result.monomials) == 1
        assert result.monomials[0].coefficient == 5.0

    def test_add_unlike_terms(self) -> None:
        """Test adding unlike terms."""
        m1 = Monomial(2.0, (("x", 1),))
        m2 = Monomial(3.0, (("y", 1),))
        result = m1 + m2
        assert isinstance(result, Polynomial)
        assert len(result.monomials) == 2

    def test_mul(self) -> None:
        """Test multiplying monomials."""
        m1 = Monomial(2.0, (("x", 1),))
        m2 = Monomial(3.0, (("x", 1), ("y", 1)))
        result = m1 * m2
        assert result.coefficient == 6.0
        assert result.variables == (("x", 2), ("y", 1))

    def test_repr(self) -> None:
        """Test string representation."""
        m = Monomial(2.0, (("x", 1), ("y", 2)))
        assert "2.0" in repr(m)
        assert "x" in repr(m)
        assert "y^2" in repr(m)


class TestPolynomial:
    """Tests for Polynomial."""

    def test_creation(self) -> None:
        """Test creating polynomial."""
        p = Polynomial([Monomial(2.0, (("x", 1),)), Monomial(3.0, (("y", 1),))])
        assert len(p.monomials) == 2

    def test_evaluate(self) -> None:
        """Test evaluating polynomial."""
        # 2x + 3y
        p = Polynomial([Monomial(2.0, (("x", 1),)), Monomial(3.0, (("y", 1),))])
        result = p.evaluate({"x": 2.0, "y": 3.0})
        assert result == 2 * 2 + 3 * 3

    def test_degree(self) -> None:
        """Test polynomial degree."""
        p = Polynomial([Monomial(2.0, (("x", 1),)), Monomial(3.0, (("y", 2),))])
        assert p.degree() == 2

    def test_simplify(self) -> None:
        """Test simplifying polynomial."""
        p = Polynomial(
            [
                Monomial(2.0, (("x", 1),)),
                Monomial(3.0, (("x", 1),)),
                Monomial(1.0, (("y", 1),)),
            ]
        )
        simplified = p.simplify()
        assert len(simplified.monomials) == 2

    def test_add(self) -> None:
        """Test adding polynomials."""
        p1 = Polynomial([Monomial(2.0, (("x", 1),))])
        p2 = Polynomial([Monomial(3.0, (("x", 1),))])
        result = p1 + p2
        assert result.monomials[0].coefficient == 5.0

    def test_sub(self) -> None:
        """Test subtracting polynomials."""
        p1 = Polynomial([Monomial(5.0, (("x", 1),))])
        p2 = Polynomial([Monomial(3.0, (("x", 1),))])
        result = p1 - p2
        assert result.monomials[0].coefficient == 2.0

    def test_mul(self) -> None:
        """Test multiplying polynomials."""
        # (x + 1) * (x + 2) = x^2 + 3x + 2
        p1 = Polynomial([Monomial(1.0, (("x", 1),)), Monomial(1.0, ())])
        p2 = Polynomial([Monomial(1.0, (("x", 1),)), Monomial(2.0, ())])
        result = p1 * p2
        simplified = result.simplify()
        assert len(simplified.monomials) == 3

    def test_serde(self) -> None:
        """Test serialization/deserialization."""
        p = Polynomial([Monomial(2.0, (("x", 1),)), Monomial(3.0, (("y", 2),))])
        d = p.to_dict()
        restored = Polynomial.from_dict(d)
        assert restored == p

    def test_repr(self) -> None:
        """Test string representation."""
        p = Polynomial([Monomial(2.0, (("x", 1),)), Monomial(3.0, (("y", 1),))])
        assert "2.0" in repr(p)
        assert "3.0" in repr(p)


class TestInequality:
    """Tests for Inequality."""

    def test_creation(self) -> None:
        """Test creating inequality."""
        left = Polynomial([Monomial(1.0, (("x", 1),))])
        right = Polynomial([Monomial(2.0, ())])
        ineq = Inequality(left, "<=", right)
        assert ineq.operator == "<="

    def test_evaluate_le(self) -> None:
        """Test evaluating <= inequality."""
        left = Polynomial([Monomial(1.0, (("x", 1),))])
        right = Polynomial([Monomial(2.0, ())])
        ineq = Inequality(left, "<=", right)
        assert ineq.evaluate({"x": 1.0})
        assert ineq.evaluate({"x": 2.0})
        assert not ineq.evaluate({"x": 3.0})

    def test_evaluate_ge(self) -> None:
        """Test evaluating >= inequality."""
        left = Polynomial([Monomial(1.0, (("x", 1),))])
        right = Polynomial([Monomial(2.0, ())])
        ineq = Inequality(left, ">=", right)
        assert not ineq.evaluate({"x": 1.0})
        assert ineq.evaluate({"x": 2.0})
        assert ineq.evaluate({"x": 3.0})

    def test_simplify(self) -> None:
        """Test simplifying inequality."""
        left = Polynomial([Monomial(2.0, (("x", 1),)), Monomial(3.0, (("x", 1),))])
        right = Polynomial([Monomial(10.0, ())])
        ineq = Inequality(left, "<=", right)
        simplified = ineq.simplify()
        assert len(simplified.left.monomials) == 1

    def test_serde(self) -> None:
        """Test serialization/deserialization."""
        left = Polynomial([Monomial(1.0, (("x", 1),))])
        right = Polynomial([Monomial(2.0, ())])
        ineq = Inequality(left, "<=", right)
        d = ineq.to_dict()
        restored = Inequality.from_dict(d)
        assert restored == ineq

    def test_repr(self) -> None:
        """Test string representation."""
        left = Polynomial([Monomial(1.0, (("x", 1),))])
        right = Polynomial([Monomial(2.0, ())])
        ineq = Inequality(left, "<=", right)
        assert "<=" in repr(ineq)


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_variable(self) -> None:
        """Test variable factory."""
        v = variable("x")
        assert v.coefficient == 1.0
        assert v.variables == (("x", 1),)

    def test_constant(self) -> None:
        """Test constant factory."""
        c = constant(5.0)
        assert c.coefficient == 5.0
        assert c.variables == ()
