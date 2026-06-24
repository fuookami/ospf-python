"""代数公理验证测试。

Algebraic law verification tests.

测试 GroupLaw、RingLaw、FieldLaw 协议的正确实现。
Tests correct implementation of GroupLaw, RingLaw,
FieldLaw protocols.
"""

from __future__ import annotations

from ospf_python.math.algebra.law import (
    FieldLaw,
    GroupLaw,
    RingLaw,
)
from ospf_python.math.algebra.number import (
    Floating,
    Integer,
    Rational,
)

# ── Concrete law implementation for testing ──────────────────────


class _FloatingGroupLaw:
    """浮点数群公理验证器。/ Floating group law verifier."""

    def verify_associativity(self, *, a: object, b: object, c: object) -> bool:
        left = (a + b) + c  # type: ignore[operator]
        right = a + (b + c)  # type: ignore[operator]
        return left == right

    def verify_identity(self, *, a: object, zero: object) -> bool:
        return (a + zero == a) and (zero + a == a)  # type: ignore[operator]

    def verify_inverse(self, *, a: object, neg_a: object, zero: object) -> bool:
        return (a + neg_a == zero) and (neg_a + a == zero)  # type: ignore[operator]


class _FloatingRingLaw(_FloatingGroupLaw):
    """浮点数环公理验证器。/ Floating ring law verifier."""

    def verify_distributivity(self, *, a: object, b: object, c: object) -> bool:
        left = a * (b + c)  # type: ignore[operator]
        right = (a * b) + (a * c)  # type: ignore[operator]
        return left == right


class _FloatingFieldLaw(_FloatingRingLaw):
    """浮点数域公理验证器。/ Floating field law verifier."""

    def verify_multiplicative_inverse(
        self, *, a: object, inv_a: object, one: object
    ) -> bool:
        return (a * inv_a == one) and (inv_a * a == one)  # type: ignore[operator]


# ── GroupLaw tests ────────────────────────────────────────────────


class TestGroupLaw:
    """群公理测试。"""

    def test_group_law_is_protocol(self) -> None:
        """GroupLaw 是运行时可检查协议。"""
        verifier = _FloatingGroupLaw()
        assert isinstance(verifier, GroupLaw)

    def test_associativity_integers(self) -> None:
        """整数加法满足结合律。"""
        v = _FloatingGroupLaw()
        assert v.verify_associativity(a=Integer(1), b=Integer(2), c=Integer(3))

    def test_associativity_floating(self) -> None:
        """浮点加法满足结合律。"""
        v = _FloatingGroupLaw()
        assert v.verify_associativity(a=Floating(1.0), b=Floating(2.0), c=Floating(3.0))

    def test_identity_element(self) -> None:
        """零是加法单位元。"""
        v = _FloatingGroupLaw()
        assert v.verify_identity(a=Integer(42), zero=Integer(0))

    def test_inverse_element(self) -> None:
        """a + (-a) == 0。"""
        v = _FloatingGroupLaw()
        assert v.verify_inverse(a=Integer(7), neg_a=Integer(-7), zero=Integer(0))

    def test_associativity_rational(self) -> None:
        """有理数加法满足结合律。"""
        v = _FloatingGroupLaw()
        assert v.verify_associativity(
            a=Rational(1, 2),
            b=Rational(1, 3),
            c=Rational(1, 6),
        )


# ── RingLaw tests ─────────────────────────────────────────────────


class TestRingLaw:
    """环公理测试。"""

    def test_ring_law_is_protocol(self) -> None:
        """RingLaw 是运行时可检查协议。"""
        verifier = _FloatingRingLaw()
        assert isinstance(verifier, RingLaw)

    def test_distributivity_integers(self) -> None:
        """整数乘法对加法满足分配律。"""
        v = _FloatingRingLaw()
        assert v.verify_distributivity(a=Integer(2), b=Integer(3), c=Integer(4))

    def test_distributivity_floating(self) -> None:
        """浮点乘法对加法满足分配律。"""
        v = _FloatingRingLaw()
        assert v.verify_distributivity(
            a=Floating(1.5),
            b=Floating(2.0),
            c=Floating(3.0),
        )


# ── FieldLaw tests ────────────────────────────────────────────────


class TestFieldLaw:
    """域公理测试。"""

    def test_field_law_is_protocol(self) -> None:
        """FieldLaw 是运行时可检查协议。"""
        verifier = _FloatingFieldLaw()
        assert isinstance(verifier, FieldLaw)

    def test_multiplicative_inverse(self) -> None:
        """浮点乘法逆元验证。"""
        v = _FloatingFieldLaw()
        a = Floating(5.0)
        inv_a = Floating(0.2)
        assert v.verify_multiplicative_inverse(a=a, inv_a=inv_a, one=Floating(1.0))

    def test_multiplicative_inverse_rational(self) -> None:
        """有理数乘法逆元验证。"""
        v = _FloatingFieldLaw()
        a = Rational(2, 3)
        inv_a = Rational(3, 2)
        assert v.verify_multiplicative_inverse(a=a, inv_a=inv_a, one=Rational(1))
