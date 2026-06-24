"""规范多项式测试。

Canonical polynomial tests.

测试 CanonicalPolynomial 的创建、次数和求值。
Tests CanonicalPolynomial creation, degree, and evaluation.
"""

from __future__ import annotations

from ospf_python.math.symbol.monomial.canonical_monomial import (
    CanonicalMonomial,
)
from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)
from ospf_python.math.symbol.symbol import Symbol

# ── CanonicalPolynomial creation ────────────────────────────────


class TestCanonicalPolynomialCreation:
    """规范多项式创建测试。"""

    def test_zero(self) -> None:
        """零多项式。/ Zero polynomial."""
        p = CanonicalPolynomial.zero()
        assert p.is_zero
        assert p.term_count == 0

    def test_constant(self) -> None:
        """常数多项式。/ Constant polynomial."""
        p = CanonicalPolynomial.constant(5.0)
        assert p.term_count == 1
        assert p.degree == 0

    def test_of_monomials(self) -> None:
        """从单项式创建。/ Create from monomials."""
        x = Symbol.create("x")
        m1 = CanonicalMonomial.single(x)
        m2 = CanonicalMonomial.constant(3.0)
        p = CanonicalPolynomial.of(m1, m2)
        assert p.term_count == 2


# ── CanonicalPolynomial properties ──────────────────────────────


class TestCanonicalPolynomialProperties:
    """规范多项式属性测试。"""

    def test_degree_empty(self) -> None:
        """空多项式次数为 0。/ Empty polynomial degree is 0."""
        p = CanonicalPolynomial.zero()
        assert p.degree == 0

    def test_degree_linear(self) -> None:
        """线性多项式次数为 1。/ Linear polynomial degree is 1."""
        x = Symbol.create("x")
        p = CanonicalPolynomial.of(CanonicalMonomial.single(x))
        assert p.degree == 1

    def test_is_zero(self) -> None:
        """零多项式检查。/ Zero polynomial check."""
        assert CanonicalPolynomial.zero().is_zero
        assert not CanonicalPolynomial.constant(1.0).is_zero


# ── CanonicalPolynomial operations ──────────────────────────────


class TestCanonicalPolynomialOperations:
    """规范多项式操作测试。"""

    def test_evaluate(self) -> None:
        """求值。/ Evaluate."""
        x = Symbol.create("x")
        p = CanonicalPolynomial.of(
            CanonicalMonomial.single(x, coefficient=2.0),
            CanonicalMonomial.constant(3.0),
        )
        assert p.evaluate({x: 5.0}) == 13.0

    def test_addition(self) -> None:
        """加法。/ Addition."""
        x = Symbol.create("x")
        p1 = CanonicalPolynomial.of(CanonicalMonomial.single(x))
        p2 = CanonicalPolynomial.constant(5.0)
        result = p1 + p2
        assert result.term_count == 2

    def test_symbols(self) -> None:
        """符号列表。/ Symbols list."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        p = CanonicalPolynomial.of(
            CanonicalMonomial.single(x),
            CanonicalMonomial.single(y),
        )
        assert x in p.symbols
        assert y in p.symbols

    def test_str_zero(self) -> None:
        """零多项式字符串。/ Zero polynomial string."""
        assert str(CanonicalPolynomial.zero()) == "0"
