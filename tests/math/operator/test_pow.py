"""幂运算符测试。

Power operator tests.

测试 pow_op 函数。
Tests pow_op function.
"""

from __future__ import annotations

import math

from ospf_python.math.operator.pow import pow_op

# ── pow_op ──────────────────────────────────────────────────────


class TestPowOp:
    """幂运算符测试。"""

    def test_basic_power(self) -> None:
        """基本幂运算。/ Basic power."""
        assert pow_op(2.0, 3.0) == 8.0

    def test_zero_exponent(self) -> None:
        """零指数。/ Zero exponent."""
        assert pow_op(5.0, 0.0) == 1.0

    def test_one_exponent(self) -> None:
        """单位指数。/ One exponent."""
        assert pow_op(7.0, 1.0) == 7.0

    def test_negative_exponent(self) -> None:
        """负指数。/ Negative exponent."""
        assert math.isclose(pow_op(2.0, -1.0), 0.5)

    def test_fractional_exponent(self) -> None:
        """小数指数。/ Fractional exponent."""
        assert math.isclose(pow_op(4.0, 0.5), 2.0)

    def test_zero_base(self) -> None:
        """零底数。/ Zero base."""
        assert pow_op(0.0, 5.0) == 0.0

    def test_square(self) -> None:
        """平方。/ Square."""
        assert pow_op(3.0, 2.0) == 9.0
