"""指数运算符测试。

Exponential operator tests.

测试 exp_op、exp2_op、exp10_op 函数。
Tests exp_op, exp2_op, exp10_op functions.
"""

from __future__ import annotations

import math

from ospf_python.math.operator.exp import exp2_op, exp10_op, exp_op

# ── exp_op ──────────────────────────────────────────────────────


class TestExpOp:
    """自然指数运算符测试。"""

    def test_exp_zero(self) -> None:
        """e^0 = 1。/ e^0 = 1."""
        assert exp_op(0.0) == 1.0

    def test_exp_one(self) -> None:
        """e^1 = e。/ e^1 = e."""
        assert math.isclose(exp_op(1.0), math.e)

    def test_exp_negative(self) -> None:
        """e^(-1)。/ e^(-1)."""
        assert math.isclose(exp_op(-1.0), 1.0 / math.e)

    def test_exp_two(self) -> None:
        """e^2。/ e^2."""
        assert math.isclose(exp_op(2.0), math.e**2)


# ── exp2_op ─────────────────────────────────────────────────────


class TestExp2Op:
    """以 2 为底指数运算符测试。"""

    def test_exp2_zero(self) -> None:
        """2^0 = 1。/ 2^0 = 1."""
        assert exp2_op(0.0) == 1.0

    def test_exp2_ten(self) -> None:
        """2^10 = 1024。/ 2^10 = 1024."""
        assert exp2_op(10.0) == 1024.0

    def test_exp2_one(self) -> None:
        """2^1 = 2。/ 2^1 = 2."""
        assert exp2_op(1.0) == 2.0


# ── exp10_op ────────────────────────────────────────────────────


class TestExp10Op:
    """以 10 为底指数运算符测试。"""

    def test_exp10_zero(self) -> None:
        """10^0 = 1。/ 10^0 = 1."""
        assert exp10_op(0.0) == 1.0

    def test_exp10_two(self) -> None:
        """10^2 = 100。/ 10^2 = 100."""
        assert exp10_op(2.0) == 100.0

    def test_exp10_three(self) -> None:
        """10^3 = 1000。/ 10^3 = 1000."""
        assert exp10_op(3.0) == 1000.0
