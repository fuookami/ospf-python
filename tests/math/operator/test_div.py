"""整除运算符测试。

Integer division operator tests.

测试 div_op 函数。
Tests div_op function.
"""

from __future__ import annotations

from ospf_python.math.operator.div import div_op

# ── div_op ──────────────────────────────────────────────────────


class TestDivOp:
    """整除运算符测试。"""

    def test_exact_division(self) -> None:
        """整除。/ Exact division."""
        assert div_op(10, 3) == 3

    def test_even_division(self) -> None:
        """整除无余数。/ Even division."""
        assert div_op(12, 4) == 3

    def test_negative_division(self) -> None:
        """负数整除。/ Negative division."""
        assert div_op(-7, 2) == -4

    def test_zero_dividend(self) -> None:
        """被除数为零。/ Zero dividend."""
        assert div_op(0, 5) == 0

    def test_large_division(self) -> None:
        """大数整除。/ Large division."""
        assert div_op(100, 7) == 14

    def test_one_divisor(self) -> None:
        """除数为 1。/ Divisor is 1."""
        assert div_op(42, 1) == 42
