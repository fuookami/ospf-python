"""幺半群协议测试。

Monoid protocol tests.

测试 Monoid 协议的运行时检查和单位元属性。
Tests Monoid protocol runtime checks and identity properties.
"""

from __future__ import annotations

from ospf_python.math.algebra.concept import Monoid
from ospf_python.math.algebra.number import (
    Floating,
    Integer,
    Rational,
)

# ── Monoid protocol ─────────────────────────────────────────────


class TestMonoidProtocol:
    """幺半群协议测试。"""

    def test_integer_is_monoid(self) -> None:
        """整数满足幺半群协议。/ Integer satisfies Monoid."""
        assert isinstance(Integer(1), Monoid)

    def test_floating_is_monoid(self) -> None:
        """浮点数满足幺半群协议。/ Floating satisfies Monoid."""
        assert isinstance(Floating(1.0), Monoid)

    def test_rational_is_monoid(self) -> None:
        """有理数满足幺半群协议。/ Rational satisfies Monoid."""
        assert isinstance(Rational(1, 2), Monoid)

    def test_integer_zero_identity(self) -> None:
        """整数零是加法单位元。/ Integer zero is additive identity."""
        a = Integer(42)
        zero = a.zero
        assert a + zero == a
        assert zero + a == a

    def test_floating_zero_identity(self) -> None:
        """浮点零是加法单位元。/ Floating zero is additive identity."""
        a = Floating(3.14)
        zero = a.zero
        assert a + zero == a

    def test_rational_zero_identity(self) -> None:
        """有理数零是加法单位元。/ Rational zero is additive identity."""
        a = Rational(3, 7)
        zero = a.zero
        assert a + zero == a

    def test_zero_value(self) -> None:
        """零值正确。/ Zero value correct."""
        assert Integer(5).zero == Integer(0)
        assert Floating(5.0).zero == Floating(0.0)
        assert Rational(5, 1).zero == Rational(0)
