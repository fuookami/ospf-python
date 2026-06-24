"""线性多项式测试。

Linear polynomial tests.

测试 LinearPolynomial 的创建、次数和求值。
Tests LinearPolynomial creation, degree, and evaluation.
"""

from __future__ import annotations

from ospf_python.math.symbol.monomial.linear_monomial import (
    LinearMonomial,
)
from ospf_python.math.symbol.polynomial.linear_polynomial import (
    LinearPolynomial,
)
from ospf_python.math.symbol.symbol import Symbol

# ── LinearPolynomial creation ───────────────────────────────────


class TestLinearPolynomialCreation:
    """线性多项式创建测试。"""

    def test_zero(self) -> None:
        """零多项式。/ Zero polynomial."""
        p = LinearPolynomial.zero()
        assert p.is_zero
        assert p.term_count == 0

    def test_of_constant(self) -> None:
        """常数多项式。/ Constant polynomial."""
        p = LinearPolynomial.of_constant(5.0)
        assert p.is_constant
        assert p.constant == 5.0

    def test_of_monomials(self) -> None:
        """从单项式创建。/ Create from monomials."""
        x = Symbol.create("x")
        m = LinearMonomial.create(x, coefficient=2.0)
        p = LinearPolynomial.of(m, constant=3.0)
        assert p.term_count == 1
        assert p.constant == 3.0


# ── LinearPolynomial properties ─────────────────────────────────


class TestLinearPolynomialProperties:
    """线性多项式属性测试。"""

    def test_degree_zero(self) -> None:
        """零多项式次数为 0。/ Zero polynomial degree is 0."""
        assert LinearPolynomial.zero().degree == 0

    def test_degree_one(self) -> None:
        """线性多项式次数为 1。/ Linear polynomial degree is 1."""
        x = Symbol.create("x")
        p = LinearPolynomial.of(LinearMonomial.create(x))
        assert p.degree == 1

    def test_is_constant(self) -> None:
        """常数多项式检查。/ Constant polynomial check."""
        assert LinearPolynomial.of_constant(5.0).is_constant

    def test_is_zero(self) -> None:
        """零多项式检查。/ Zero polynomial check."""
        assert LinearPolynomial.zero().is_zero
        assert not LinearPolynomial.of_constant(1.0).is_zero


# ── LinearPolynomial operations ─────────────────────────────────


class TestLinearPolynomialOperations:
    """线性多项式操作测试。"""

    def test_evaluate(self) -> None:
        """求值。/ Evaluate."""
        x = Symbol.create("x")
        p = LinearPolynomial.of(
            LinearMonomial.create(x, coefficient=2.0),
            constant=3.0,
        )
        assert p.evaluate({x: 5.0}) == 13.0

    def test_addition(self) -> None:
        """加法。/ Addition."""
        x = Symbol.create("x")
        p1 = LinearPolynomial.of(LinearMonomial.create(x), constant=1.0)
        p2 = LinearPolynomial.of(LinearMonomial.create(x), constant=2.0)
        result = p1 + p2
        assert result.term_count == 2
        assert result.constant == 3.0

    def test_symbols(self) -> None:
        """符号列表。/ Symbols list."""
        x = Symbol.create("x")
        p = LinearPolynomial.of(LinearMonomial.create(x))
        assert x in p.symbols
