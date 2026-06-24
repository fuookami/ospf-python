"""规范不等式测试。

Canonical inequality tests.

测试 CanonicalInequality 的创建、取反和反转。
Tests CanonicalInequality creation, negation, and reversal.
"""

from __future__ import annotations

from ospf_python.math.symbol.inequality.canonical_inequality import (
    CanonicalInequality,
)
from ospf_python.math.symbol.inequality.comparison import Comparison

# ── CanonicalInequality creation ────────────────────────────────


class TestCanonicalInequalityCreation:
    """规范不等式创建测试。"""

    def test_creation(self) -> None:
        """创建不等式。/ Create inequality."""
        ineq = CanonicalInequality(
            left="a",
            right="b",
            comparison=Comparison.LE,
        )
        assert ineq.left == "a"
        assert ineq.right == "b"
        assert ineq.comparison == Comparison.LE

    def test_is_linear_default(self) -> None:
        """默认非线性。/ Default not linear."""
        ineq = CanonicalInequality(
            left=1,
            right=2,
            comparison=Comparison.LT,
        )
        assert not ineq.is_linear

    def test_is_quadratic_default(self) -> None:
        """默认非二次。/ Default not quadratic."""
        ineq = CanonicalInequality(
            left=1,
            right=2,
            comparison=Comparison.LT,
        )
        assert not ineq.is_quadratic


# ── CanonicalInequality negation ────────────────────────────────


class TestCanonicalInequalityNegation:
    """规范不等式取反测试。"""

    def test_negate_le(self) -> None:
        """取反 <= 为 >。/ Negate LE to GT."""
        ineq = CanonicalInequality(
            left=1,
            right=2,
            comparison=Comparison.LE,
        )
        neg = ineq.negated()
        assert neg.comparison == Comparison.GT

    def test_negate_lt(self) -> None:
        """取反 < 为 >=。/ Negate LT to GE."""
        ineq = CanonicalInequality(
            left=1,
            right=2,
            comparison=Comparison.LT,
        )
        neg = ineq.negated()
        assert neg.comparison == Comparison.GE

    def test_negate_preserves_operands(self) -> None:
        """取反保留操作数。/ Negation preserves operands."""
        ineq = CanonicalInequality(
            left="x",
            right="y",
            comparison=Comparison.EQ,
        )
        neg = ineq.negated()
        assert neg.left == "x"
        assert neg.right == "y"


# ── CanonicalInequality reversal ────────────────────────────────


class TestCanonicalInequalityReversal:
    """规范不等式反转测试。"""

    def test_reverse(self) -> None:
        """反转不等式。/ Reverse inequality."""
        ineq = CanonicalInequality(
            left="a",
            right="b",
            comparison=Comparison.LT,
        )
        rev = ineq.reversed()
        assert rev.left == "b"
        assert rev.right == "a"
        assert rev.comparison == Comparison.GT

    def test_reverse_le(self) -> None:
        """反转 <= 为 >=。/ Reverse LE to GE."""
        ineq = CanonicalInequality(
            left=1,
            right=2,
            comparison=Comparison.LE,
        )
        rev = ineq.reversed()
        assert rev.comparison == Comparison.GE
