"""交换环协议测试。

Commutative ring protocol tests.

测试 CommutativeRing 协议的运行时检查和乘法交换律。
Tests CommutativeRing protocol runtime checks and
multiplicative commutativity.
"""

from __future__ import annotations

from ospf_python.math.algebra.concept import CommutativeRing
from ospf_python.math.algebra.number import (
    Floating,
    Integer,
    Rational,
)

# ── CommutativeRing protocol ────────────────────────────────────


class TestCommutativeRingProtocol:
    """交换环协议测试。"""

    def test_integer_is_commutative_ring(self) -> None:
        """整数满足交换环。/ Integer satisfies CommutativeRing."""
        assert isinstance(Integer(1), CommutativeRing)

    def test_floating_is_commutative_ring(self) -> None:
        """浮点满足交换环。/ Floating satisfies CommutativeRing."""
        assert isinstance(Floating(1.0), CommutativeRing)

    def test_rational_is_commutative_ring(self) -> None:
        """有理数满足交换环。/ Rational satisfies CommutativeRing."""
        assert isinstance(Rational(1, 2), CommutativeRing)

    def test_integer_mult_commutativity(self) -> None:
        """整数乘法交换律。/ Integer mult commutativity."""
        a, b = Integer(3), Integer(5)
        assert a * b == b * a

    def test_floating_mult_commutativity(self) -> None:
        """浮点乘法交换律。/ Floating mult commutativity."""
        a = Floating(2.5)
        b = Floating(4.0)
        assert a * b == b * a

    def test_rational_mult_commutativity(self) -> None:
        """有理数乘法交换律。/ Rational mult commutativity."""
        a = Rational(2, 3)
        b = Rational(3, 5)
        assert a * b == b * a
