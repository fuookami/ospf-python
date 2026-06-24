"""频率单位测试。/ Frequency unit tests.

测试频率单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision for frequency units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.frequency import (
    GIGAHERTZ,
    HERTZ,
    KILOHERTZ,
    MEGAHERTZ,
    REVOLUTIONS_PER_MINUTE,
)


class TestFrequencyToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_hertz_to_si(self) -> None:
        """赫兹到 SI。/ Hertz to SI."""
        assert HERTZ.to_si(1.0) == 1.0

    def test_kilohertz_to_si(self) -> None:
        """千赫到 SI。/ Kilohertz to SI."""
        assert KILOHERTZ.to_si(1.0) == 1000.0

    def test_megahertz_to_si(self) -> None:
        """兆赫到 SI。/ Megahertz to SI."""
        assert MEGAHERTZ.to_si(1.0) == 1e6

    def test_gigahertz_to_si(self) -> None:
        """吉赫到 SI。/ Gigahertz to SI."""
        assert GIGAHERTZ.to_si(1.0) == 1e9

    def test_rpm_to_si(self) -> None:
        """转每分到 SI。/ RPM to SI."""
        result = REVOLUTIONS_PER_MINUTE.to_si(60.0)
        assert result == pytest.approx(1.0)


class TestFrequencyRoundTrip:
    """往返转换测试 / Round-trip tests."""

    def test_roundtrip(self) -> None:
        """往返转换。/ Roundtrip."""
        original = 440.0
        si = HERTZ.to_si(original)
        back = HERTZ.from_si(si)
        assert back == pytest.approx(original)
