"""力单位测试。/ Force unit tests.

测试力单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision for force units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.force import (
    DYNE,
    KILOGRAM_FORCE,
    KILONEWTON,
    NEWTON,
    POUND_FORCE,
)


class TestForceToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_newton_to_si(self) -> None:
        """牛顿到 SI。/ Newton to SI."""
        assert NEWTON.to_si(1.0) == 1.0

    def test_kilonewton_to_si(self) -> None:
        """千牛到 SI。/ Kilonewton to SI."""
        assert KILONEWTON.to_si(1.0) == 1000.0

    def test_dyne_to_si(self) -> None:
        """达因到 SI。/ Dyne to SI."""
        assert DYNE.to_si(1.0) == pytest.approx(1e-5)

    def test_pound_force_to_si(self) -> None:
        """磅力到 SI。/ Pound-force to SI."""
        result = POUND_FORCE.to_si(1.0)
        assert result == pytest.approx(4.44822, rel=1e-4)

    def test_kilogram_force_to_si(self) -> None:
        """千克力到 SI。/ Kilogram-force to SI."""
        result = KILOGRAM_FORCE.to_si(1.0)
        assert result == pytest.approx(9.80665, rel=1e-4)


class TestForceRoundTrip:
    """往返转换测试 / Round-trip tests."""

    def test_roundtrip(self) -> None:
        """往返转换。/ Roundtrip."""
        original = 50.0
        si = NEWTON.to_si(original)
        back = NEWTON.from_si(si)
        assert back == pytest.approx(original)
