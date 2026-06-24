"""体积单位测试。/ Volume unit tests.

测试体积单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision for volume units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.volume import (
    CUBIC_METER,
    LITER,
    MILLILITER,
)


class TestVolumeToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_cubic_meter_to_si(self) -> None:
        """立方米到 SI。/ Cubic meter to SI."""
        assert CUBIC_METER.to_si(1.0) == 1.0

    def test_liter_to_si(self) -> None:
        """升到 SI。/ Liter to SI."""
        assert LITER.to_si(1.0) == pytest.approx(0.001)

    def test_milliliter_to_si(self) -> None:
        """毫升到 SI。/ Milliliter to SI."""
        assert MILLILITER.to_si(1.0) == pytest.approx(1e-6)


class TestVolumeRoundTrip:
    """往返转换测试 / Round-trip tests."""

    def test_volume_roundtrip(self) -> None:
        """体积往返转换。/ Volume roundtrip."""
        original = 100.0
        si = LITER.to_si(original)
        back = LITER.from_si(si)
        assert back == pytest.approx(original)
