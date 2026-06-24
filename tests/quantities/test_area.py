"""面积单位测试。/ Area unit tests.

测试面积单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision for area units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.area import (
    HECTARE,
    SQUARE_KILOMETER,
    SQUARE_METER,
)


class TestAreaToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_square_meter_to_si(self) -> None:
        """平方米到 SI。/ Square meter to SI."""
        assert SQUARE_METER.to_si(1.0) == 1.0

    def test_square_kilometer_to_si(self) -> None:
        """平方千米到 SI。/ Square kilometer to SI."""
        assert SQUARE_KILOMETER.to_si(1.0) == pytest.approx(1e6)

    def test_hectare_to_si(self) -> None:
        """公顷到 SI。/ Hectare to SI."""
        assert HECTARE.to_si(1.0) == pytest.approx(1e4)


class TestAreaRoundTrip:
    """往返转换测试 / Round-trip tests."""

    def test_area_roundtrip(self) -> None:
        """面积往返转换。/ Area roundtrip."""
        original = 2.5
        si = HECTARE.to_si(original)
        back = HECTARE.from_si(si)
        assert back == pytest.approx(original)
