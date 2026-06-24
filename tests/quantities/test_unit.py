"""单位测试。/ Unit tests.

测试各种物理单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision
for various physical units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.area import (
    HECTARE,
    SQUARE_KILOMETER,
    SQUARE_METER,
)
from ospf_python.quantities.unit.length import (
    CENTIMETER,
    FOOT,
    INCH,
    KILOMETER,
    METER,
    MILE,
    MILLIMETER,
)
from ospf_python.quantities.unit.mass import (
    GRAM,
    KILOGRAM,
    MILLIGRAM,
    OUNCE,
    POUND,
)
from ospf_python.quantities.unit.physical_unit import (
    PhysicalUnit,
)
from ospf_python.quantities.unit.time_unit import (
    DAY,
    HOUR,
    MILLISECOND,
    MINUTE,
    SECOND,
)
from ospf_python.quantities.unit.volume import (
    CUBIC_METER,
    LITER,
    MILLILITER,
)

# ── 长度 ─────────────────────────────────────────────────────────


class TestLengthUnits:
    """长度单位测试。"""

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

    def test_length_roundtrip(self) -> None:
        """长度往返转换。/ Length roundtrip."""
        original = 42.0
        si = KILOMETER.to_si(original)
        back = KILOMETER.from_si(si)
        assert back == pytest.approx(original)

    def test_length_protocol(self) -> None:
        """长度满足 PhysicalUnit 协议。
        Length satisfies PhysicalUnit protocol.
        """
        assert isinstance(METER, PhysicalUnit)
        assert isinstance(KILOMETER, PhysicalUnit)


# ── 质量 ─────────────────────────────────────────────────────────


class TestMassUnits:
    """质量单位测试。"""

    def test_kilogram_to_si(self) -> None:
        """千克到 SI。/ Kilogram to SI."""
        assert KILOGRAM.to_si(1.0) == 1.0

    def test_gram_to_si(self) -> None:
        """克到 SI。/ Gram to SI."""
        assert GRAM.to_si(1.0) == 0.001

    def test_milligram_to_si(self) -> None:
        """毫克到 SI。/ Milligram to SI."""
        assert MILLIGRAM.to_si(1.0) == pytest.approx(1e-6)

    def test_pound_to_si(self) -> None:
        """磅到 SI。/ Pound to SI."""
        result = POUND.to_si(1.0)
        assert result == pytest.approx(0.45359237, rel=1e-6)

    def test_ounce_to_si(self) -> None:
        """盎司到 SI。/ Ounce to SI."""
        result = OUNCE.to_si(1.0)
        assert result == pytest.approx(0.0283495, rel=1e-4)

    def test_mass_roundtrip(self) -> None:
        """质量往返转换。/ Mass roundtrip."""
        original = 5.5
        si = POUND.to_si(original)
        back = POUND.from_si(si)
        assert back == pytest.approx(original)


# ── 时间 ─────────────────────────────────────────────────────────


class TestTimeUnits:
    """时间单位测试。"""

    def test_second_to_si(self) -> None:
        """秒到 SI。/ Second to SI."""
        assert SECOND.to_si(1.0) == 1.0

    def test_millisecond_to_si(self) -> None:
        """毫秒到 SI。/ Millisecond to SI."""
        assert MILLISECOND.to_si(1.0) == pytest.approx(0.001)

    def test_minute_to_si(self) -> None:
        """分钟到 SI。/ Minute to SI."""
        assert MINUTE.to_si(1.0) == pytest.approx(60.0)

    def test_hour_to_si(self) -> None:
        """小时到 SI。/ Hour to SI."""
        assert HOUR.to_si(1.0) == pytest.approx(3600.0)

    def test_day_to_si(self) -> None:
        """天到 SI。/ Day to SI."""
        assert DAY.to_si(1.0) == pytest.approx(86400.0)

    def test_time_protocol(self) -> None:
        """时间满足 PhysicalUnit 协议。
        Time satisfies PhysicalUnit protocol.
        """
        assert isinstance(SECOND, PhysicalUnit)
        assert isinstance(HOUR, PhysicalUnit)


# ── 面积 ─────────────────────────────────────────────────────────


class TestAreaUnits:
    """面积单位测试。"""

    def test_square_meter_to_si(self) -> None:
        """平方米到 SI。/ Square meter to SI."""
        assert SQUARE_METER.to_si(1.0) == 1.0

    def test_square_kilometer_to_si(self) -> None:
        """平方千米到 SI。/ Square kilometer to SI."""
        assert SQUARE_KILOMETER.to_si(1.0) == pytest.approx(1e6)

    def test_hectare_to_si(self) -> None:
        """公顷到 SI。/ Hectare to SI."""
        assert HECTARE.to_si(1.0) == pytest.approx(1e4)

    def test_area_roundtrip(self) -> None:
        """面积往返转换。/ Area roundtrip."""
        original = 2.5
        si = HECTARE.to_si(original)
        back = HECTARE.from_si(si)
        assert back == pytest.approx(original)


# ── 体积 ─────────────────────────────────────────────────────────


class TestVolumeUnits:
    """体积单位测试。"""

    def test_cubic_meter_to_si(self) -> None:
        """立方米到 SI。/ Cubic meter to SI."""
        assert CUBIC_METER.to_si(1.0) == 1.0

    def test_liter_to_si(self) -> None:
        """升到 SI。/ Liter to SI."""
        assert LITER.to_si(1.0) == pytest.approx(0.001)

    def test_milliliter_to_si(self) -> None:
        """毫升到 SI。/ Milliliter to SI."""
        assert MILLILITER.to_si(1.0) == pytest.approx(1e-6)

    def test_volume_roundtrip(self) -> None:
        """体积往返转换。/ Volume roundtrip."""
        original = 100.0
        si = LITER.to_si(original)
        back = LITER.from_si(si)
        assert back == pytest.approx(original)
