"""取余运算符测试。

Remainder operator tests.

测试 rem_op 函数。
Tests rem_op function.
"""

from __future__ import annotations

from ospf_python.math.operator.rem import rem_op

# ── rem_op ──────────────────────────────────────────────────────


class TestRemOp:
    """取余运算符测试。"""

    def test_basic_remainder(self) -> None:
        """基本取余。/ Basic remainder."""
        assert rem_op(10, 3) == 1

    def test_even_division(self) -> None:
        """整除余零。/ Even division remainder zero."""
        assert rem_op(12, 4) == 0

    def test_negative_dividend(self) -> None:
        """负被除数。/ Negative dividend."""
        assert rem_op(-7, 3) == 2

    def test_float_remainder(self) -> None:
        """浮点取余。/ Float remainder."""
        assert rem_op(5.5, 2.0) == 1.5

    def test_large_divisor(self) -> None:
        """除数大于被除数。/ Divisor larger than dividend."""
        assert rem_op(3, 10) == 3

    def test_one_divisor(self) -> None:
        """除数为 1。/ Divisor is 1."""
        assert rem_op(42, 1) == 0
