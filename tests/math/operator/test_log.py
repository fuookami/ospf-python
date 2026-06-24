"""对数运算符测试。

Logarithm operator tests.

测试 log_op、log2_op、log10_op 函数。
Tests log_op, log2_op, log10_op functions.
"""

from __future__ import annotations

import math

from ospf_python.math.operator.log import log2_op, log10_op, log_op

# ── log_op ──────────────────────────────────────────────────────


class TestLogOp:
    """自然对数运算符测试。"""

    def test_log_one(self) -> None:
        """ln(1) = 0。/ ln(1) = 0."""
        assert log_op(1.0) == 0.0

    def test_log_e(self) -> None:
        """ln(e) = 1。/ ln(e) = 1."""
        assert math.isclose(log_op(math.e), 1.0)

    def test_log_e_squared(self) -> None:
        """ln(e^2) = 2。/ ln(e^2) = 2."""
        assert math.isclose(log_op(math.e**2), 2.0)


# ── log2_op ─────────────────────────────────────────────────────


class TestLog2Op:
    """以 2 为底对数运算符测试。"""

    def test_log2_one(self) -> None:
        """log2(1) = 0。/ log2(1) = 0."""
        assert log2_op(1.0) == 0.0

    def test_log2_eight(self) -> None:
        """log2(8) = 3。/ log2(8) = 3."""
        assert log2_op(8.0) == 3.0

    def test_log2_two(self) -> None:
        """log2(2) = 1。/ log2(2) = 1."""
        assert log2_op(2.0) == 1.0


# ── log10_op ────────────────────────────────────────────────────


class TestLog10Op:
    """以 10 为底对数运算符测试。"""

    def test_log10_one(self) -> None:
        """log10(1) = 0。/ log10(1) = 0."""
        assert log10_op(1.0) == 0.0

    def test_log10_thousand(self) -> None:
        """log10(1000) = 3。/ log10(1000) = 3."""
        assert log10_op(1000.0) == 3.0

    def test_log10_ten(self) -> None:
        """log10(10) = 1。/ log10(10) = 1."""
        assert log10_op(10.0) == 1.0
