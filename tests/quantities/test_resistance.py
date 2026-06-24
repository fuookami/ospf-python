"""电阻单位测试。/ Resistance unit tests.

测试电阻单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision for resistance units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.resistance import (
    GIGAOHM,
    KILOOHM,
    MEGAOHM,
    MILLIOHM,
    OHM,
)


class TestResistanceToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_ohm_to_si(self) -> None:
        """欧姆到 SI。/ Ohm to SI."""
        assert OHM.to_si(1.0) == 1.0

    def test_milliohm_to_si(self) -> None:
        """毫欧到 SI。/ Milliohm to SI."""
        assert MILLIOHM.to_si(1.0) == pytest.approx(0.001)

    def test_kiloohm_to_si(self) -> None:
        """千欧到 SI。/ Kiloohm to SI."""
        assert KILOOHM.to_si(1.0) == 1000.0

    def test_megaohm_to_si(self) -> None:
        """兆欧到 SI。/ Megaohm to SI."""
        assert MEGAOHM.to_si(1.0) == 1e6

    def test_gigaohm_to_si(self) -> None:
        """吉欧到 SI。/ Gigaohm to SI."""
        assert GIGAOHM.to_si(1.0) == 1e9


class TestResistanceRoundTrip:
    """往返转换测试 / Round-trip tests."""

    def test_roundtrip(self) -> None:
        """往返转换。/ Roundtrip."""
        original = 100.0
        si = OHM.to_si(original)
        back = OHM.from_si(si)
        assert back == pytest.approx(original)
