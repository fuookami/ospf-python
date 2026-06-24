"""加法运算符测试。

Addition operator tests.

测试 plus_op 函数。
Tests plus_op function.
"""

from __future__ import annotations

from ospf_python.math.operator.plus import plus_op

# ── plus_op ─────────────────────────────────────────────────────


class TestPlusOp:
    """加法运算符测试。"""

    def test_basic_addition(self) -> None:
        """基本加法。/ Basic addition."""
        assert plus_op(3, 4) == 7

    def test_zero_addition(self) -> None:
        """加零。/ Add zero."""
        assert plus_op(5, 0) == 5

    def test_negative_addition(self) -> None:
        """负数加法。/ Negative addition."""
        assert plus_op(-3, -4) == -7

    def test_mixed_sign(self) -> None:
        """异号加法。/ Mixed sign addition."""
        assert plus_op(5, -3) == 2

    def test_float_addition(self) -> None:
        """浮点加法。/ Float addition."""
        assert plus_op(1.5, 2.5) == 4.0

    def test_commutativity(self) -> None:
        """交换律。/ Commutativity."""
        assert plus_op(3, 5) == plus_op(5, 3)
