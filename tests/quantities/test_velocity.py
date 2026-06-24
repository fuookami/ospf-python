"""速度单位测试。/ Velocity unit tests.

测试速度单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision for velocity units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.velocity import (
    FOOT_PER_SECOND,
    KILOMETRE_PER_HOUR,
    KNOT,
    METRE_PER_SECOND,
    MILE_PER_HOUR,
)


class TestVelocityToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_metre_per_second_to_si(self) -> None:
        """米每秒到 SI。/ m/s to SI."""
        assert METRE_PER_SECOND.to_si(1.0) == 1.0

    def test_kilometre_per_hour_to_si(self) -> None:
        """千米每小时到 SI。/ km/h to SI."""
        result = KILOMETRE_PER_HOUR.to_si(3.6)
        assert result == pytest.approx(1.0)

    def test_mile_per_hour_to_si(self) -> None:
        """英里每小时到 SI。/ mph to SI."""
        result = MILE_PER_HOUR.to_si(1.0)
        assert result == pytest.approx(0.44704, rel=1e-4)

    def test_knot_to_si(self) -> None:
        """节到 SI。/ Knot to SI."""
        result = KNOT.to_si(1.0)
        assert result == pytest.approx(0.514444, rel=1e-4)

    def test_foot_per_second_to_si(self) -> None:
        """英尺每秒到 SI。/ ft/s to SI."""
        result = FOOT_PER_SECOND.to_si(1.0)
        assert result == pytest.approx(0.3048, rel=1e-4)


class TestVelocityRoundTrip:
    """往返转换测试 / Round-trip tests."""

    def test_roundtrip(self) -> None:
        """往返转换。/ Roundtrip."""
        original = 100.0
        si = KILOMETRE_PER_HOUR.to_si(original)
        back = KILOMETRE_PER_HOUR.from_si(si)
        assert back == pytest.approx(original)
