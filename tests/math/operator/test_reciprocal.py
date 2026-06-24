"""倒数运算符测试。

Reciprocal operator tests.

测试 reciprocal_op 函数。
Tests reciprocal_op function.
"""

from __future__ import annotations

import math

from ospf_python.math.operator.reciprocal import reciprocal_op

# ── reciprocal_op ───────────────────────────────────────────────


class TestReciprocalOp:
    """倒数运算符测试。"""

    def test_reciprocal_two(self) -> None:
        """2 的倒数。/ Reciprocal of 2."""
        assert math.isclose(reciprocal_op(2.0), 0.5)

    def test_reciprocal_four(self) -> None:
        """4 的倒数。/ Reciprocal of 4."""
        assert math.isclose(reciprocal_op(4.0), 0.25)

    def test_reciprocal_one(self) -> None:
        """1 的倒数。/ Reciprocal of 1."""
        assert reciprocal_op(1.0) == 1.0

    def test_reciprocal_half(self) -> None:
        """0.5 的倒数。/ Reciprocal of 0.5."""
        assert math.isclose(reciprocal_op(0.5), 2.0)

    def test_reciprocal_negative(self) -> None:
        """负数的倒数。/ Reciprocal of negative."""
        assert math.isclose(reciprocal_op(-2.0), -0.5)

    def test_reciprocal_ten(self) -> None:
        """10 的倒数。/ Reciprocal of 10."""
        assert math.isclose(reciprocal_op(10.0), 0.1)
