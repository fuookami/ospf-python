"""域协议测试。

Field protocol tests.

测试 Field 协议的运行时检查和乘法逆元。
Tests Field protocol runtime checks and multiplicative inverse.
"""

from __future__ import annotations

from ospf_python.math.algebra.number import (
    Floating,
    Rational,
)

# ── Field protocol ──────────────────────────────────────────────


class TestFieldProtocol:
    """域协议测试。"""

    def test_floating_field_operations(self) -> None:
        """浮点支持域运算。/ Floating supports field operations."""
        a = Floating(10.0)
        b = Floating(4.0)
        assert a / b == Floating(2.5)

    def test_rational_field_operations(self) -> None:
        """有理数支持域运算。/ Rational supports field operations."""
        a = Rational(1, 2)
        b = Rational(1, 4)
        assert a / b == Rational(2, 1)

    def test_floating_division(self) -> None:
        """浮点除法。/ Floating division."""
        a = Floating(10.0)
        b = Floating(4.0)
        assert a / b == Floating(2.5)

    def test_rational_division(self) -> None:
        """有理数除法。/ Rational division."""
        a = Rational(1, 2)
        b = Rational(1, 4)
        assert a / b == Rational(2, 1)

    def test_division_by_zero_returns_zero(self) -> None:
        """除以零返回零。/ Division by zero returns zero."""
        a = Floating(5.0)
        b = Floating(0.0)
        assert a / b == Floating(0.0)

    def test_rational_division_by_zero(self) -> None:
        """有理数除以零。/ Rational division by zero."""
        a = Rational(5, 1)
        b = Rational(0, 1)
        assert a / b == Rational(0)
