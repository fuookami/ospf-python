"""长度单位测试。/ Length unit tests.

测试长度单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision for length units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.length import (
    CENTIMETER,
    FOOT,
    INCH,
    KILOMETER,
    METER,
    MILE,
    MILLIMETER,
)
from ospf_python.quantities.unit.physical_unit import PhysicalUnit


class TestLengthToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_meter_to_si(self) -> None:
        """米到 SI。/ Meter to SI."""
        assert METER.to_si(1.0) == 1.0

    def test_kilometer_to_si(self) -> None:
        """千米到 SI。/ Kilometer to SI."""
        assert KILOMETER.to_si(1.0) == 1000.0

    def test_centimeter_to_si(self) -> None:
        """厘米到 SI。/ Centimeter to SI."""
        assert CENTIMETER.to_si(100.0) == pytest.approx(1.0)

    def test_millimeter_to_si(self) -> None:
        """毫米到 SI。/ Millimeter to SI."""
        assert MILLIMETER.to_si(1000.0) == pytest.approx(1.0)

    def test_mile_to_si(self) -> None:
        """英里到 SI。/ Mile to SI."""
        result = MILE.to_si(1.0)
        assert result == pytest.approx(1609.344, rel=1e-6)

    def test_foot_to_si(self) -> None:
        """英尺到 SI。/ Foot to SI."""
        result = FOOT.to_si(1.0)
        assert result == pytest.approx(0.3048, rel=1e-6)

    def test_inch_to_si(self) -> None:
        """英寸到 SI。/ Inch to SI."""
        result = INCH.to_si(1.0)
        assert result == pytest.approx(0.0254, rel=1e-6)


class TestLengthRoundTrip:
    """往返转换测试 / Round-trip tests."""

    def test_length_roundtrip(self) -> None:
        """长度往返转换。/ Length roundtrip."""
        original = 42.0
        si = KILOMETER.to_si(original)
        back = KILOMETER.from_si(si)
        assert back == pytest.approx(original)

    def test_length_protocol(self) -> None:
        """长度满足 PhysicalUnit 协议。/ Satisfies protocol."""
        assert isinstance(METER, PhysicalUnit)
        assert isinstance(KILOMETER, PhysicalUnit)
