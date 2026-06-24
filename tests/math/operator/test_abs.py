"""绝对值运算符测试。

Absolute value operator tests.

测试 abs_op 函数。
Tests abs_op function.
"""

from __future__ import annotations

from ospf_python.math.operator.abs import abs_op

# ── abs_op ──────────────────────────────────────────────────────


class TestAbsOp:
    """绝对值运算符测试。"""

    def test_positive_int(self) -> None:
        """正整数绝对值。/ Positive int absolute value."""
        assert abs_op(5) == 5

    def test_negative_int(self) -> None:
        """负整数绝对值。/ Negative int absolute value."""
        assert abs_op(-3) == 3

    def test_zero_int(self) -> None:
        """零的绝对值。/ Zero absolute value."""
        assert abs_op(0) == 0

    def test_positive_float(self) -> None:
        """正浮点绝对值。/ Positive float absolute value."""
        assert abs_op(3.14) == 3.14

    def test_negative_float(self) -> None:
        """负浮点绝对值。/ Negative float absolute value."""
        assert abs_op(-2.5) == 2.5

    def test_large_negative(self) -> None:
        """大负数绝对值。/ Large negative absolute value."""
        assert abs_op(-1000000) == 1000000
