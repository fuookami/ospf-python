"""能量单位测试。/ Energy unit tests.

测试能量单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision for energy units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.energy import (
    BTU,
    CALORIE,
    ELECTRON_VOLT,
    JOULE,
    KILOCALORIE,
    KILOJOULE,
    KILOWATT_HOUR,
    WATT_HOUR,
)


class TestEnergyToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_joule_to_si(self) -> None:
        """焦耳到 SI。/ Joule to SI."""
        assert JOULE.to_si(1.0) == 1.0

    def test_kilojoule_to_si(self) -> None:
        """千焦到 SI。/ Kilojoule to SI."""
        assert KILOJOULE.to_si(1.0) == 1000.0

    def test_calorie_to_si(self) -> None:
        """卡路里到 SI。/ Calorie to SI."""
        assert CALORIE.to_si(1.0) == pytest.approx(4.184)

    def test_kilocalorie_to_si(self) -> None:
        """千卡到 SI。/ Kilocalorie to SI."""
        assert KILOCALORIE.to_si(1.0) == pytest.approx(4184.0)

    def test_watt_hour_to_si(self) -> None:
        """瓦时到 SI。/ Watt-hour to SI."""
        assert WATT_HOUR.to_si(1.0) == pytest.approx(3600.0)

    def test_kilowatt_hour_to_si(self) -> None:
        """千瓦时到 SI。/ Kilowatt-hour to SI."""
        assert KILOWATT_HOUR.to_si(1.0) == pytest.approx(3_600_000.0)

    def test_btu_to_si(self) -> None:
        """BTU 到 SI。/ BTU to SI."""
        assert BTU.to_si(1.0) == pytest.approx(1055.06, rel=1e-3)

    def test_electron_volt_to_si(self) -> None:
        """电子伏特到 SI。/ Electron volt to SI."""
        result = ELECTRON_VOLT.to_si(1.0)
        assert result == pytest.approx(1.602176634e-19)


class TestEnergyRoundTrip:
    """往返转换测试 / Round-trip tests."""

    def test_roundtrip(self) -> None:
        """往返转换。/ Roundtrip."""
        original = 100.0
        si = KILOJOULE.to_si(original)
        back = KILOJOULE.from_si(si)
        assert back == pytest.approx(original)
