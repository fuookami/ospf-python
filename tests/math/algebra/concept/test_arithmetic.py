"""算术协议测试。

Arithmetic protocol tests.

测试 Arithmetic 协议的运行时检查。
Tests Arithmetic protocol runtime checks.
"""

from __future__ import annotations

from ospf_python.math.algebra.concept import Arithmetic
from ospf_python.math.algebra.number import (
    Floating,
    Integer,
    Rational,
)

# ── Arithmetic protocol ─────────────────────────────────────────


class TestArithmeticProtocol:
    """算术协议测试。"""

    def test_integer_is_arithmetic(self) -> None:
        """整数满足算术协议。/ Integer satisfies Arithmetic."""
        assert isinstance(Integer(5), Arithmetic)

    def test_floating_is_arithmetic(self) -> None:
        """浮点满足算术协议。/ Floating satisfies Arithmetic."""
        assert isinstance(Floating(3.14), Arithmetic)

    def test_rational_is_arithmetic(self) -> None:
        """有理数满足算术协议。/ Rational satisfies Arithmetic."""
        assert isinstance(Rational(1, 3), Arithmetic)

    def test_arithmetic_operations(self) -> None:
        """算术运算。/ Arithmetic operations."""
        a = Integer(10)
        b = Integer(3)
        assert (a + b) == Integer(13)
        assert (a - b) == Integer(7)
        assert (a * b) == Integer(30)
        assert (-a) == Integer(-10)

    def test_floating_division(self) -> None:
        """浮点除法。/ Floating division."""
        a = Floating(10.0)
        b = Floating(4.0)
        assert a / b == Floating(2.5)
