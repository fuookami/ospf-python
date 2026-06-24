"""温度单位测试。/ Temperature unit tests.

测试温度单位的 SI 转换，包括偏移量处理。
Tests SI conversion for temperature units, including offsets.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.temperature import (
    CELSIUS,
    FAHRENHEIT,
    KELVIN,
    RANKINE,
)


class TestTemperatureToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_kelvin_to_si(self) -> None:
        """开尔文到 SI。/ Kelvin to SI."""
        assert KELVIN.to_si(300.0) == 300.0

    def test_celsius_to_si(self) -> None:
        """摄氏度到 SI。/ Celsius to SI."""
        assert CELSIUS.to_si(0.0) == pytest.approx(273.15)
        assert CELSIUS.to_si(100.0) == pytest.approx(373.15)

    def test_fahrenheit_to_si(self) -> None:
        """华氏度到 SI。/ Fahrenheit to SI."""
        result = FAHRENHEIT.to_si(32.0)
        assert result == pytest.approx(273.15, abs=0.1)

    def test_rankine_to_si(self) -> None:
        """兰氏度到 SI。/ Rankine to SI."""
        result = RANKINE.to_si(491.67)
        assert result == pytest.approx(273.15, abs=0.1)


class TestTemperatureFromSI:
    """从 SI 转换测试 / From SI tests."""

    def test_celsius_from_si(self) -> None:
        """从 SI 到摄氏度。/ From SI to Celsius."""
        assert CELSIUS.from_si(273.15) == pytest.approx(0.0)
        assert CELSIUS.from_si(373.15) == pytest.approx(100.0)

    def test_kelvin_from_si(self) -> None:
        """从 SI 到开尔文。/ From SI to Kelvin."""
        assert KELVIN.from_si(300.0) == pytest.approx(300.0)
