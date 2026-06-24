"""功率单位测试。/ Power unit tests.

测试功率单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision for power units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.power import (
    HORSEPOWER,
    HORSEPOWER_METRIC,
    KILOWATT,
    MEGAWATT,
    MILLIWATT,
    WATT,
)


class TestPowerToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_watt_to_si(self) -> None:
        """瓦特到 SI。/ Watt to SI."""
        assert WATT.to_si(1.0) == 1.0

    def test_kilowatt_to_si(self) -> None:
        """千瓦到 SI。/ Kilowatt to SI."""
        assert KILOWATT.to_si(1.0) == 1000.0

    def test_megawatt_to_si(self) -> None:
        """兆瓦到 SI。/ Megawatt to SI."""
        assert MEGAWATT.to_si(1.0) == 1e6

    def test_milliwatt_to_si(self) -> None:
        """毫瓦到 SI。/ Milliwatt to SI."""
        assert MILLIWATT.to_si(1.0) == pytest.approx(0.001)

    def test_horsepower_to_si(self) -> None:
        """马力到 SI。/ Horsepower to SI."""
        result = HORSEPOWER.to_si(1.0)
        assert result == pytest.approx(745.7, rel=1e-3)

    def test_horsepower_metric_to_si(self) -> None:
        """公制马力到 SI。/ Metric hp to SI."""
        result = HORSEPOWER_METRIC.to_si(1.0)
        assert result == pytest.approx(735.5, rel=1e-3)


class TestPowerRoundTrip:
    """往返转换测试 / Round-trip tests."""

    def test_roundtrip(self) -> None:
        """往返转换。/ Roundtrip."""
        original = 75.0
        si = WATT.to_si(original)
        back = WATT.from_si(si)
        assert back == pytest.approx(original)
