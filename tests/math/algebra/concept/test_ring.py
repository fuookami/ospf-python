"""环协议测试。

Ring protocol tests.

测试 Ring 协议的运行时检查和分配律。
Tests Ring protocol runtime checks and distributivity.
"""

from __future__ import annotations

from ospf_python.math.algebra.concept import Ring
from ospf_python.math.algebra.number import (
    Floating,
    Integer,
    Rational,
)

# ── Ring protocol ───────────────────────────────────────────────


class TestRingProtocol:
    """环协议测试。"""

    def test_integer_is_ring(self) -> None:
        """整数满足环协议。/ Integer satisfies Ring."""
        assert isinstance(Integer(1), Ring)

    def test_floating_is_ring(self) -> None:
        """浮点满足环协议。/ Floating satisfies Ring."""
        assert isinstance(Floating(1.0), Ring)

    def test_rational_is_ring(self) -> None:
        """有理数满足环协议。/ Rational satisfies Ring."""
        assert isinstance(Rational(1, 2), Ring)

    def test_distributivity_integer(self) -> None:
        """整数分配律。/ Integer distributivity."""
        a = Integer(2)
        b = Integer(3)
        c = Integer(4)
        assert a * (b + c) == (a * b) + (a * c)

    def test_distributivity_floating(self) -> None:
        """浮点分配律。/ Floating distributivity."""
        a = Floating(1.5)
        b = Floating(2.0)
        c = Floating(3.0)
        assert a * (b + c) == (a * b) + (a * c)

    def test_multiplicative_identity(self) -> None:
        """乘法单位元。/ Multiplicative identity."""
        a = Integer(7)
        one = a.one
        assert a * one == a
        assert one * a == a

    def test_one_value(self) -> None:
        """单位值正确。/ One value correct."""
        assert Integer(5).one == Integer(1)
        assert Floating(5.0).one == Floating(1.0)
        assert Rational(5, 1).one == Rational(1)
