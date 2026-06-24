"""半群协议测试。

Semigroup protocol tests.

测试 Semigroup 协议的运行时检查和基本属性。
Tests Semigroup protocol runtime checks and basic properties.
"""

from __future__ import annotations

from ospf_python.math.algebra.concept import Semigroup
from ospf_python.math.algebra.number import (
    Floating,
    Integer,
    Rational,
)

# ── Semigroup protocol ─────────────────────────────────────────


class TestSemigroupProtocol:
    """半群协议测试。"""

    def test_integer_is_semigroup(self) -> None:
        """整数满足半群协议。/ Integer satisfies Semigroup."""
        assert isinstance(Integer(1), Semigroup)

    def test_floating_is_semigroup(self) -> None:
        """浮点数满足半群协议。/ Floating satisfies Semigroup."""
        assert isinstance(Floating(1.0), Semigroup)

    def test_rational_is_semigroup(self) -> None:
        """有理数满足半群协议。/ Rational satisfies Semigroup."""
        assert isinstance(Rational(1, 2), Semigroup)

    def test_associativity_integer(self) -> None:
        """整数加法结合律。/ Integer addition associativity."""
        a, b, c = Integer(1), Integer(2), Integer(3)
        assert (a + b) + c == a + (b + c)

    def test_associativity_floating(self) -> None:
        """浮点加法结合律。/ Floating addition associativity."""
        a = Floating(1.0)
        b = Floating(2.0)
        c = Floating(3.0)
        assert (a + b) + c == a + (b + c)

    def test_associativity_rational(self) -> None:
        """有理数加法结合律。/ Rational addition associativity."""
        a = Rational(1, 2)
        b = Rational(1, 3)
        c = Rational(1, 6)
        assert (a + b) + c == a + (b + c)

    def test_integer_add_identity(self) -> None:
        """整数加法恒等式。/ Integer addition identity."""
        a = Integer(42)
        b = Integer(0)
        assert a + b == a
