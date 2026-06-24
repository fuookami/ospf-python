"""二次多项式测试。

Quadratic polynomial tests.

测试 QuadraticPolynomial 的创建、次数和求值。
Tests QuadraticPolynomial creation, degree, and evaluation.
"""

from __future__ import annotations

from ospf_python.math.symbol.monomial.quadratic_monomial import (
    QuadraticMonomial,
)
from ospf_python.math.symbol.polynomial.quadratic_polynomial import (
    QuadraticPolynomial,
)
from ospf_python.math.symbol.symbol import Symbol

# ── QuadraticPolynomial creation ────────────────────────────────


class TestQuadraticPolynomialCreation:
    """二次多项式创建测试。"""

    def test_zero(self) -> None:
        """零多项式。/ Zero polynomial."""
        p = QuadraticPolynomial.zero()
        assert p.is_zero

    def test_of_quadratic(self) -> None:
        """从二次单项式创建。/ Create from quadratic monomials."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(lhs=x, rhs=y)
        p = QuadraticPolynomial.of(m)
        assert len(p.quadratic_terms) == 1

    def test_of_with_linear(self) -> None:
        """带线性项创建。/ Create with linear terms."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(lhs=x, rhs=y)
        p = QuadraticPolynomial.of(m, linear={x: 2.0}, constant=3.0)
        assert p.linear_terms[x] == 2.0
        assert p.constant == 3.0


# ── QuadraticPolynomial properties ──────────────────────────────


class TestQuadraticPolynomialProperties:
    """二次多项式属性测试。"""

    def test_degree_zero(self) -> None:
        """零多项式次数为 0。/ Zero polynomial degree is 0."""
        assert QuadraticPolynomial.zero().degree == 0

    def test_degree_two(self) -> None:
        """二次多项式次数为 2。/ Quadratic polynomial degree is 2."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(lhs=x, rhs=y)
        p = QuadraticPolynomial.of(m)
        assert p.degree == 2

    def test_is_zero(self) -> None:
        """零多项式检查。/ Zero polynomial check."""
        assert QuadraticPolynomial.zero().is_zero


# ── QuadraticPolynomial operations ──────────────────────────────


class TestQuadraticPolynomialOperations:
    """二次多项式操作测试。"""

    def test_evaluate(self) -> None:
        """求值。/ Evaluate."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(coefficient=2.0, lhs=x, rhs=y)
        p = QuadraticPolynomial.of(m, constant=1.0)
        assert p.evaluate({x: 3.0, y: 4.0}) == 25.0

    def test_symbols(self) -> None:
        """符号列表。/ Symbols list."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(lhs=x, rhs=y)
        p = QuadraticPolynomial.of(m)
        assert x in p.symbols
        assert y in p.symbols
