"""规范单项式测试。

Canonical monomial tests.

测试 CanonicalMonomial 的创建、次数和求值。
Tests CanonicalMonomial creation, degree, and evaluation.
"""

from __future__ import annotations

from ospf_python.math.symbol.monomial.canonical_monomial import (
    CanonicalMonomial,
)
from ospf_python.math.symbol.symbol import Symbol

# ── CanonicalMonomial creation ──────────────────────────────────


class TestCanonicalMonomialCreation:
    """规范单项式创建测试。"""

    def test_constant(self) -> None:
        """常数单项式。/ Constant monomial."""
        m = CanonicalMonomial.constant(5.0)
        assert m.coefficient == 5.0
        assert m.is_constant

    def test_single_symbol(self) -> None:
        """单符号单项式。/ Single-symbol monomial."""
        x = Symbol.create("x")
        m = CanonicalMonomial.single(x)
        assert m.coefficient == 1.0
        assert x in m.powers

    def test_single_with_coefficient(self) -> None:
        """带系数的单符号。/ Single-symbol with coefficient."""
        x = Symbol.create("x")
        m = CanonicalMonomial.single(x, coefficient=3.0)
        assert m.coefficient == 3.0

    def test_single_with_power(self) -> None:
        """带幂次的单符号。/ Single-symbol with power."""
        x = Symbol.create("x")
        m = CanonicalMonomial.single(x, power=2)
        assert m.powers[x] == 2


# ── CanonicalMonomial degree ────────────────────────────────────


class TestCanonicalMonomialDegree:
    """规范单项式次数测试。"""

    def test_constant_degree_zero(self) -> None:
        """常数次数为 0。/ Constant degree is 0."""
        assert CanonicalMonomial.constant(1.0).degree == 0

    def test_linear_degree(self) -> None:
        """线性次数为 1。/ Linear degree is 1."""
        x = Symbol.create("x")
        assert CanonicalMonomial.single(x).degree == 1

    def test_quadratic_degree(self) -> None:
        """二次次数为 2。/ Quadratic degree is 2."""
        x = Symbol.create("x")
        assert CanonicalMonomial.single(x, power=2).degree == 2


# ── CanonicalMonomial evaluate ──────────────────────────────────


class TestCanonicalMonomialEvaluate:
    """规范单项式求值测试。"""

    def test_constant_evaluate(self) -> None:
        """常数求值。/ Constant evaluation."""
        m = CanonicalMonomial.constant(7.0)
        assert m.evaluate({}) == 7.0

    def test_linear_evaluate(self) -> None:
        """线性求值。/ Linear evaluation."""
        x = Symbol.create("x")
        m = CanonicalMonomial.single(x, coefficient=3.0)
        assert m.evaluate({x: 2.0}) == 6.0

    def test_missing_binding_zero(self) -> None:
        """缺失绑定默认为 0。/ Missing binding defaults to 0."""
        x = Symbol.create("x")
        m = CanonicalMonomial.single(x)
        assert m.evaluate({}) == 0.0


# ── CanonicalMonomial multiplication ────────────────────────────


class TestCanonicalMonomialMultiplication:
    """规范单项式乘法测试。"""

    def test_multiply_same_symbol(self) -> None:
        """同符号乘法。/ Same symbol multiplication."""
        x = Symbol.create("x")
        a = CanonicalMonomial.single(x, power=2)
        b = CanonicalMonomial.single(x, power=3)
        result = a * b
        assert result.powers[x] == 5

    def test_multiply_different_symbols(self) -> None:
        """不同符号乘法。/ Different symbol multiplication."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        a = CanonicalMonomial.single(x)
        b = CanonicalMonomial.single(y)
        result = a * b
        assert result.powers[x] == 1
        assert result.powers[y] == 1
