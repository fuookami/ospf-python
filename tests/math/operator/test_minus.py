"""减法运算符测试。

Subtraction operator tests.

测试 minus_op 函数。
Tests minus_op function.
"""

from __future__ import annotations

from ospf_python.math.operator.minus import minus_op

# ── minus_op ────────────────────────────────────────────────────


class TestMinusOp:
    """减法运算符测试。"""

    def test_basic_subtraction(self) -> None:
        """基本减法。/ Basic subtraction."""
        assert minus_op(10, 3) == 7

    def test_result_zero(self) -> None:
        """结果为零。/ Result is zero."""
        assert minus_op(5, 5) == 0

    def test_negative_result(self) -> None:
        """负结果。/ Negative result."""
        assert minus_op(3, 7) == -4

    def test_float_subtraction(self) -> None:
        """浮点减法。/ Float subtraction."""
        assert minus_op(5.5, 2.3) == 3.2

    def test_zero_minus(self) -> None:
        """零减。/ Zero minus."""
        assert minus_op(0, 5) == -5

    def test_large_values(self) -> None:
        """大值减法。/ Large value subtraction."""
        assert minus_op(1000000, 999999) == 1
