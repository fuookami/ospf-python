"""力矩单位测试。/ Torque unit tests.

测试力矩单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision for torque units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.torque import (
    DYNE_CENTIMETRE,
    FOOT_POUND_FORCE,
    INCH_POUND_FORCE,
    KILOGRAM_FORCE_METRE,
    KILONEWTON_METRE,
    NEWTON_METRE,
)


class TestTorqueToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_newton_metre_to_si(self) -> None:
        """牛顿米到 SI。/ Newton-metre to SI."""
        assert NEWTON_METRE.to_si(1.0) == 1.0

    def test_kilonewton_metre_to_si(self) -> None:
        """千牛米到 SI。/ Kilonewton-metre to SI."""
        assert KILONEWTON_METRE.to_si(1.0) == 1000.0

    def test_foot_pound_force_to_si(self) -> None:
        """英尺磅力到 SI。/ Foot-pound-force to SI."""
        result = FOOT_POUND_FORCE.to_si(1.0)
        assert result == pytest.approx(1.35582, rel=1e-4)

    def test_inch_pound_force_to_si(self) -> None:
        """英寸磅力到 SI。/ Inch-pound-force to SI."""
        result = INCH_POUND_FORCE.to_si(1.0)
        assert result == pytest.approx(0.11298, rel=1e-3)

    def test_kilogram_force_metre_to_si(self) -> None:
        """千克力米到 SI。/ kgf-metre to SI."""
        result = KILOGRAM_FORCE_METRE.to_si(1.0)
        assert result == pytest.approx(9.80665, rel=1e-4)

    def test_dyne_centimetre_to_si(self) -> None:
        """达因厘米到 SI。/ Dyne-centimetre to SI."""
        assert DYNE_CENTIMETRE.to_si(1.0) == pytest.approx(1e-7)


class TestTorqueRoundTrip:
    """往返转换测试 / Round-trip tests."""

    def test_roundtrip(self) -> None:
        """往返转换。/ Roundtrip."""
        original = 50.0
        si = NEWTON_METRE.to_si(original)
        back = NEWTON_METRE.from_si(si)
        assert back == pytest.approx(original)
