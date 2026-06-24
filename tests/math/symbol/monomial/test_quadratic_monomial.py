"""二次单项式测试。

Quadratic monomial tests.

测试 QuadraticMonomial 的创建、求值和操作。
Tests QuadraticMonomial creation, evaluation, and operations.
"""

from __future__ import annotations

from ospf_python.math.symbol.monomial.quadratic_monomial import (
    QuadraticMonomial,
)
from ospf_python.math.symbol.symbol import Symbol

# ── QuadraticMonomial creation ──────────────────────────────────


class TestQuadraticMonomialCreation:
    """二次单项式创建测试。"""

    def test_create(self) -> None:
        """创建二次单项式。/ Create quadratic monomial."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(lhs=x, rhs=y)
        assert m.coefficient == 1.0
        assert m.lhs == x
        assert m.rhs == y

    def test_create_with_coefficient(self) -> None:
        """带系数创建。/ Create with coefficient."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(coefficient=2.5, lhs=x, rhs=y)
        assert m.coefficient == 2.5


# ── QuadraticMonomial properties ────────────────────────────────


class TestQuadraticMonomialProperties:
    """二次单项式属性测试。"""

    def test_degree_always_two(self) -> None:
        """次数始终为 2。/ Degree is always 2."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(lhs=x, rhs=y)
        assert m.degree == 2

    def test_is_square_true(self) -> None:
        """平方项。/ Square term."""
        x = Symbol.create("x")
        m = QuadraticMonomial.create(lhs=x, rhs=x)
        assert m.is_square

    def test_is_square_false(self) -> None:
        """非平方项。/ Not square term."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(lhs=x, rhs=y)
        assert not m.is_square

    def test_symbols_deduplicated(self) -> None:
        """符号去重。/ Symbols deduplicated."""
        x = Symbol.create("x")
        m = QuadraticMonomial.create(lhs=x, rhs=x)
        assert m.symbols == [x]


# ── QuadraticMonomial operations ────────────────────────────────


class TestQuadraticMonomialOperations:
    """二次单项式操作测试。"""

    def test_evaluate(self) -> None:
        """求值。/ Evaluate."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(coefficient=2.0, lhs=x, rhs=y)
        assert m.evaluate(3.0, 4.0) == 24.0

    def test_negate(self) -> None:
        """取反。/ Negate."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(coefficient=3.0, lhs=x, rhs=y)
        neg = m.negate()
        assert neg.coefficient == -3.0

    def test_scale(self) -> None:
        """缩放。/ Scale."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(coefficient=2.0, lhs=x, rhs=y)
        scaled = m.scale(3.0)
        assert scaled.coefficient == 6.0
