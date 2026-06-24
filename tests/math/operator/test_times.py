"""乘法运算符测试。

Multiplication operator tests.

测试 times_op 函数。
Tests times_op function.
"""

from __future__ import annotations

from ospf_python.math.operator.times import times_op

# ── times_op ────────────────────────────────────────────────────


class TestTimesOp:
    """乘法运算符测试。"""

    def test_basic_multiplication(self) -> None:
        """基本乘法。/ Basic multiplication."""
        assert times_op(3, 4) == 12

    def test_multiply_by_zero(self) -> None:
        """乘以零。/ Multiply by zero."""
        assert times_op(5, 0) == 0

    def test_multiply_by_one(self) -> None:
        """乘以一。/ Multiply by one."""
        assert times_op(7, 1) == 7

    def test_negative_multiplication(self) -> None:
        """负数乘法。/ Negative multiplication."""
        assert times_op(-3, 4) == -12

    def test_both_negative(self) -> None:
        """双负数乘法。/ Both negative multiplication."""
        assert times_op(-3, -4) == 12

    def test_float_multiplication(self) -> None:
        """浮点乘法。/ Float multiplication."""
        assert times_op(2.5, 4.0) == 10.0

    def test_commutativity(self) -> None:
        """交换律。/ Commutativity."""
        assert times_op(3, 5) == times_op(5, 3)
