"""代数协议符合性测试。

Algebraic protocol conformance tests.

验证数值类型是否正确实现各代数协议。
Verifies that numeric types correctly implement
algebraic protocols.
"""

from __future__ import annotations

from ospf_python.math.algebra.concept import (
    Arithmetic,
    HasHalf,
    HasOne,
    HasZero,
    Number,
    RealNumber,
    Semigroup,
)
from ospf_python.math.algebra.number import (
    Floating,
    Integer,
    Rational,
)

# ── Protocol conformance ─────────────────────────────────────────


class TestSemigroupConformance:
    """半群协议符合性测试。"""

    def test_integer_is_semigroup(self) -> None:
        """整数满足半群协议。/ Integer satisfies Semigroup."""
        assert isinstance(Integer(1), Semigroup)

    def test_floating_is_semigroup(self) -> None:
        """浮点数满足半群协议。/ Floating satisfies Semigroup."""
        assert isinstance(Floating(1.0), Semigroup)

    def test_rational_is_semigroup(self) -> None:
        """有理数满足半群协议。/ Rational satisfies Semigroup."""
        assert isinstance(Rational(1, 2), Semigroup)


class TestArithmeticConformance:
    """算术协议符合性测试。"""

    def test_integer_is_arithmetic(self) -> None:
        """整数满足算术协议。/ Integer satisfies Arithmetic."""
        assert isinstance(Integer(5), Arithmetic)

    def test_floating_is_arithmetic(self) -> None:
        """浮点数满足算术协议。/ Floating satisfies Arithmetic."""
        assert isinstance(Floating(3.14), Arithmetic)

    def test_rational_is_arithmetic(self) -> None:
        """有理数满足算术协议。/ Rational satisfies Arithmetic."""
        assert isinstance(Rational(1, 3), Arithmetic)


class TestNumberConformance:
    """数值协议符合性测试。"""

    def test_floating_is_number(self) -> None:
        """浮点数满足数值协议。/ Floating satisfies Number."""
        assert isinstance(Floating(1.0), Number)

    def test_integer_is_number(self) -> None:
        """整数满足数值协议。/ Integer satisfies Number."""
        assert isinstance(Integer(42), Number)

    def test_rational_is_number(self) -> None:
        """有理数满足数值协议。/ Rational satisfies Number."""
        assert isinstance(Rational(3, 4), Number)


class TestRealNumberConformance:
    """实数协议符合性测试。"""

    def test_floating_is_real(self) -> None:
        """浮点数满足实数协议。/ Floating satisfies RealNumber."""
        assert isinstance(Floating(2.71), RealNumber)

    def test_integer_is_real(self) -> None:
        """整数满足实数协议。/ Integer satisfies RealNumber."""
        assert isinstance(Integer(-5), RealNumber)

    def test_rational_is_real(self) -> None:
        """有理数满足实数协议。/ Rational satisfies RealNumber."""
        assert isinstance(Rational(7, 11), RealNumber)


class TestConstantProviderConformance:
    """常量提供者协议符合性测试。"""

    def test_floating_has_zero(self) -> None:
        """浮点数提供零值。/ Floating provides zero."""
        assert isinstance(Floating(0.0), HasZero)

    def test_floating_has_one(self) -> None:
        """浮点数提供单位值。/ Floating provides one."""
        assert isinstance(Floating(1.0), HasOne)

    def test_floating_has_half(self) -> None:
        """浮点数提供半值。/ Floating provides half."""
        assert isinstance(Floating(0.5), HasHalf)
