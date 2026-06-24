"""数值协议测试。

Number protocol tests.

测试 Number 和 RealNumber 协议的运行时检查。
Tests Number and RealNumber protocol runtime checks.
"""

from __future__ import annotations

from ospf_python.math.algebra.concept import Number, RealNumber
from ospf_python.math.algebra.number import (
    Floating,
    Integer,
    Rational,
)

# ── Number protocol ─────────────────────────────────────────────


class TestNumberProtocol:
    """数值协议测试。"""

    def test_floating_is_number(self) -> None:
        """浮点满足数值协议。/ Floating satisfies Number."""
        assert isinstance(Floating(1.0), Number)

    def test_integer_is_number(self) -> None:
        """整数满足数值协议。/ Integer satisfies Number."""
        assert isinstance(Integer(42), Number)

    def test_rational_is_number(self) -> None:
        """有理数满足数值协议。/ Rational satisfies Number."""
        assert isinstance(Rational(3, 4), Number)


# ── RealNumber protocol ─────────────────────────────────────────


class TestRealNumberProtocol:
    """实数协议测试。"""

    def test_floating_is_real(self) -> None:
        """浮点满足实数协议。/ Floating satisfies RealNumber."""
        assert isinstance(Floating(2.71), RealNumber)

    def test_integer_is_real(self) -> None:
        """整数满足实数协议。/ Integer satisfies RealNumber."""
        assert isinstance(Integer(-5), RealNumber)

    def test_rational_is_real(self) -> None:
        """有理数满足实数协议。/ Rational satisfies RealNumber."""
        assert isinstance(Rational(7, 11), RealNumber)

    def test_real_number_ordering(self) -> None:
        """实数排序。/ Real number ordering."""
        assert Integer(3) < Integer(5)
        assert Floating(1.0) < Floating(2.0)
