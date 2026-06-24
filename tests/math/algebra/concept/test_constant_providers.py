"""常量提供者协议测试。

Constant provider protocol tests.

测试 HasZero、HasOne、HasTwo、HasHalf 等协议。
Tests HasZero, HasOne, HasTwo, HasHalf protocols.
"""

from __future__ import annotations

import math

from ospf_python.math.algebra.concept import (
    HasBounds,
    HasFive,
    HasHalf,
    HasInfinity,
    HasNaN,
    HasOne,
    HasTen,
    HasThree,
    HasTwo,
    HasZero,
)
from ospf_python.math.algebra.number import Floating

# ── HasZero ─────────────────────────────────────────────────────


class TestHasZero:
    """零值提供者测试。"""

    def test_floating_has_zero(self) -> None:
        """浮点提供零值。/ Floating provides zero."""
        assert isinstance(Floating(0.0), HasZero)

    def test_zero_value(self) -> None:
        """零值正确。/ Zero value correct."""
        assert Floating(0.0).zero == Floating(0.0)


# ── HasOne ──────────────────────────────────────────────────────


class TestHasOne:
    """单位值提供者测试。"""

    def test_floating_has_one(self) -> None:
        """浮点提供单位值。/ Floating provides one."""
        assert isinstance(Floating(1.0), HasOne)

    def test_one_value(self) -> None:
        """单位值正确。/ One value correct."""
        assert Floating(0.0).one == Floating(1.0)


# ── HasTwo ──────────────────────────────────────────────────────


class TestHasTwo:
    """二值提供者测试。"""

    def test_floating_has_two(self) -> None:
        """浮点提供二值。/ Floating provides two."""
        assert isinstance(Floating(0.0), HasTwo)

    def test_two_value(self) -> None:
        """二值正确。/ Two value correct."""
        assert Floating(0.0).two == Floating(2.0)


# ── HasHalf ─────────────────────────────────────────────────────


class TestHasHalf:
    """半值提供者测试。"""

    def test_floating_has_half(self) -> None:
        """浮点提供半值。/ Floating provides half."""
        assert isinstance(Floating(0.0), HasHalf)

    def test_half_value(self) -> None:
        """半值正确。/ Half value correct."""
        assert Floating(0.0).half == Floating(0.5)


# ── HasFive / HasThree / HasTen ─────────────────────────────────


class TestOtherConstants:
    """其他常量提供者测试。"""

    def test_floating_has_five(self) -> None:
        """浮点提供五值。/ Floating provides five."""
        assert isinstance(Floating(0.0), HasFive)

    def test_floating_has_three(self) -> None:
        """浮点提供三值。/ Floating provides three."""
        assert isinstance(Floating(0.0), HasThree)

    def test_floating_has_ten(self) -> None:
        """浮点提供十值。/ Floating provides ten."""
        assert isinstance(Floating(0.0), HasTen)

    def test_five_value(self) -> None:
        """五值正确。/ Five value correct."""
        assert Floating(0.0).five == Floating(5.0)

    def test_three_value(self) -> None:
        """三值正确。/ Three value correct."""
        assert Floating(0.0).three == Floating(3.0)

    def test_ten_value(self) -> None:
        """十值正确。/ Ten value correct."""
        assert Floating(0.0).ten == Floating(10.0)


# ── HasBounds / HasInfinity / HasNaN ────────────────────────────


class TestBoundsAndSpecial:
    """边界和特殊值提供者测试。"""

    def test_floating_has_bounds(self) -> None:
        """浮点提供边界值。/ Floating provides bounds."""
        assert isinstance(Floating(0.0), HasBounds)

    def test_floating_has_infinity(self) -> None:
        """浮点提供无穷大。/ Floating provides infinity."""
        assert isinstance(Floating(0.0), HasInfinity)

    def test_floating_has_nan(self) -> None:
        """浮点提供 NaN。/ Floating provides NaN."""
        assert isinstance(Floating(0.0), HasNaN)

    def test_positive_inf(self) -> None:
        """正无穷。/ Positive infinity."""
        assert Floating(0.0).positive_inf == Floating(math.inf)

    def test_negative_inf(self) -> None:
        """负无穷。/ Negative infinity."""
        assert Floating(0.0).negative_inf == Floating(-math.inf)

    def test_nan_value(self) -> None:
        """NaN 值。/ NaN value."""
        val = Floating(0.0).nan
        assert math.isnan(val.value)
