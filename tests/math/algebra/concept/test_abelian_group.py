"""阿贝尔群协议测试。

Abelian group protocol tests.

测试 AbelianGroup 协议的运行时检查和交换律。
Tests AbelianGroup protocol runtime checks and commutativity.
"""

from __future__ import annotations

from ospf_python.math.algebra.concept import AbelianGroup
from ospf_python.math.algebra.number import (
    Floating,
    Integer,
    Rational,
)

# ── AbelianGroup protocol ───────────────────────────────────────


class TestAbelianGroupProtocol:
    """阿贝尔群协议测试。"""

    def test_integer_is_abelian(self) -> None:
        """整数满足阿贝尔群。/ Integer satisfies AbelianGroup."""
        assert isinstance(Integer(1), AbelianGroup)

    def test_floating_is_abelian(self) -> None:
        """浮点满足阿贝尔群。/ Floating satisfies AbelianGroup."""
        assert isinstance(Floating(1.0), AbelianGroup)

    def test_rational_is_abelian(self) -> None:
        """有理数满足阿贝尔群。/ Rational satisfies AbelianGroup."""
        assert isinstance(Rational(1, 2), AbelianGroup)

    def test_integer_commutativity(self) -> None:
        """整数加法交换律。/ Integer addition commutativity."""
        a, b = Integer(3), Integer(5)
        assert a + b == b + a

    def test_floating_commutativity(self) -> None:
        """浮点加法交换律。/ Floating addition commutativity."""
        a = Floating(1.5)
        b = Floating(2.5)
        assert a + b == b + a

    def test_rational_commutativity(self) -> None:
        """有理数加法交换律。/ Rational addition commutativity."""
        a = Rational(1, 3)
        b = Rational(2, 5)
        assert a + b == b + a
