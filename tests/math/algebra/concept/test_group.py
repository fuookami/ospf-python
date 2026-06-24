"""群协议测试。

Group protocol tests.

测试 Group 协议的运行时检查和逆元属性。
Tests Group protocol runtime checks and inverse properties.
"""

from __future__ import annotations

from ospf_python.math.algebra.concept import Group
from ospf_python.math.algebra.number import (
    Floating,
    Integer,
    Rational,
)

# ── Group protocol ──────────────────────────────────────────────


class TestGroupProtocol:
    """群协议测试。"""

    def test_integer_is_group(self) -> None:
        """整数满足群协议。/ Integer satisfies Group."""
        assert isinstance(Integer(1), Group)

    def test_floating_is_group(self) -> None:
        """浮点数满足群协议。/ Floating satisfies Group."""
        assert isinstance(Floating(1.0), Group)

    def test_rational_is_group(self) -> None:
        """有理数满足群协议。/ Rational satisfies Group."""
        assert isinstance(Rational(1, 2), Group)

    def test_integer_inverse(self) -> None:
        """整数逆元。/ Integer inverse."""
        a = Integer(7)
        assert a + (-a) == a.zero

    def test_floating_inverse(self) -> None:
        """浮点逆元。/ Floating inverse."""
        a = Floating(3.14)
        assert a + (-a) == a.zero

    def test_rational_inverse(self) -> None:
        """有理数逆元。/ Rational inverse."""
        a = Rational(3, 7)
        assert a + (-a) == a.zero

    def test_subtraction(self) -> None:
        """减法。/ Subtraction."""
        a = Integer(10)
        b = Integer(3)
        assert a - b == Integer(7)

    def test_negation(self) -> None:
        """取反。/ Negation."""
        assert -Integer(5) == Integer(-5)
        assert -Floating(2.5) == Floating(-2.5)
        assert -Rational(3, 4) == Rational(-3, 4)
