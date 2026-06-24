"""电压单位测试。/ Voltage unit tests.

测试电压单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision for voltage units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.voltage import (
    KILOVOLT,
    MICROVOLT,
    MILLIVOLT,
    VOLT,
)


class TestVoltageToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_volt_to_si(self) -> None:
        """伏特到 SI。/ Volt to SI."""
        assert VOLT.to_si(1.0) == 1.0

    def test_millivolt_to_si(self) -> None:
        """毫伏到 SI。/ Millivolt to SI."""
        assert MILLIVOLT.to_si(1.0) == pytest.approx(0.001)

    def test_microvolt_to_si(self) -> None:
        """微伏到 SI。/ Microvolt to SI."""
        assert MICROVOLT.to_si(1.0) == pytest.approx(1e-6)

    def test_kilovolt_to_si(self) -> None:
        """千伏到 SI。/ Kilovolt to SI."""
        assert KILOVOLT.to_si(1.0) == 1000.0


class TestVoltageRoundTrip:
    """往返转换测试 / Round-trip tests."""

    def test_roundtrip(self) -> None:
        """往返转换。/ Roundtrip."""
        original = 220.0
        si = VOLT.to_si(original)
        back = VOLT.from_si(si)
        assert back == pytest.approx(original)
