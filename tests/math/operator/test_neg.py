"""取反运算符测试。

Negation operator tests.

测试 neg_op 函数。
Tests neg_op function.
"""

from __future__ import annotations

from ospf_python.math.operator.neg import neg_op

# ── neg_op ──────────────────────────────────────────────────────


class TestNegOp:
    """取反运算符测试。"""

    def test_positive_negation(self) -> None:
        """正数取反。/ Positive negation."""
        assert neg_op(5) == -5

    def test_negative_negation(self) -> None:
        """负数取反。/ Negative negation."""
        assert neg_op(-3) == 3

    def test_zero_negation(self) -> None:
        """零取反。/ Zero negation."""
        assert neg_op(0) == 0

    def test_float_negation(self) -> None:
        """浮点取反。/ Float negation."""
        assert neg_op(2.5) == -2.5

    def test_double_negation(self) -> None:
        """双重取反。/ Double negation."""
        assert neg_op(neg_op(7)) == 7
