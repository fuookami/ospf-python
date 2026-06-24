"""线性不等式测试。

Linear inequality tests.

测试 LinearInequality 的创建、取反和反转。
Tests LinearInequality creation, negation, and reversal.
"""

from __future__ import annotations

from ospf_python.math.symbol.inequality.comparison import Comparison
from ospf_python.math.symbol.inequality.linear_inequality import (
    LinearInequality,
)

# ── LinearInequality creation ───────────────────────────────────


class TestLinearInequalityCreation:
    """线性不等式创建测试。"""

    def test_creation(self) -> None:
        """创建线性不等式。/ Create linear inequality."""
        ineq = LinearInequality(
            left="a",
            right="b",
            comparison=Comparison.LE,
        )
        assert ineq.left == "a"
        assert ineq.right == "b"
        assert ineq.comparison == Comparison.LE

    def test_is_linear(self) -> None:
        """线性不等式。/ Is linear."""
        ineq = LinearInequality(
            left=1,
            right=2,
            comparison=Comparison.LT,
        )
        assert ineq.is_linear


# ── LinearInequality negation ───────────────────────────────────


class TestLinearInequalityNegation:
    """线性不等式取反测试。"""

    def test_negate_returns_linear(self) -> None:
        """取反返回线性不等式。/ Negation returns linear."""
        ineq = LinearInequality(
            left="x",
            right="y",
            comparison=Comparison.LE,
        )
        neg = ineq.negated()
        assert isinstance(neg, LinearInequality)
        assert neg.comparison == Comparison.GT

    def test_negate_preserves_operands(self) -> None:
        """取反保留操作数。/ Negation preserves operands."""
        ineq = LinearInequality(
            left="x",
            right="y",
            comparison=Comparison.EQ,
        )
        neg = ineq.negated()
        assert neg.left == "x"
        assert neg.right == "y"


# ── LinearInequality reversal ───────────────────────────────────


class TestLinearInequalityReversal:
    """线性不等式反转测试。"""

    def test_reverse_returns_linear(self) -> None:
        """反转返回线性不等式。/ Reversal returns linear."""
        ineq = LinearInequality(
            left="x",
            right="y",
            comparison=Comparison.LT,
        )
        rev = ineq.reversed()
        assert isinstance(rev, LinearInequality)
        assert rev.left == "y"
        assert rev.right == "x"

    def test_reverse_comparison(self) -> None:
        """反转比较运算符。/ Reverse comparison operator."""
        ineq = LinearInequality(
            left=1,
            right=2,
            comparison=Comparison.LE,
        )
        rev = ineq.reversed()
        assert rev.comparison == Comparison.GE
