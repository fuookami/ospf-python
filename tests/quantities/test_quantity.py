"""物理量测试。/ Physical quantity tests.

测试创建、转换、加减乘除、不可变性和辅助函数。
Tests creation, conversion, arithmetic, immutability,
and helper functions.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from ospf_python.quantities.quantity.duration_extensions import (
    from_hours,
    from_minutes,
    to_timedelta,
)
from ospf_python.quantities.quantity.min_max import (
    max_quantity,
    min_quantity,
)
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.quantity.value_range import (
    QuantityValueRange,
)
from ospf_python.quantities.unit.length import (
    CENTIMETER,
    KILOMETER,
    METER,
    MILLIMETER,
)
from ospf_python.quantities.unit.mass import GRAM, KILOGRAM
from ospf_python.quantities.unit.time_unit import HOUR, SECOND

# ── 创建 ─────────────────────────────────────────────────────────


class TestQuantityCreation:
    """物理量创建测试。"""

    def test_create_with_float(self) -> None:
        """浮点值创建。/ Create with float value."""
        q = Quantity(value=1.5, unit=METER)
        assert q.value == 1.5
        assert q.unit.symbol == "m"

    def test_create_with_int(self) -> None:
        """整数值创建。/ Create with int value."""
        q = Quantity(value=10, unit=KILOGRAM)
        assert q.value == 10
        assert q.unit.symbol == "kg"

    def test_create_zero(self) -> None:
        """零值创建。/ Create zero quantity."""
        q = Quantity(value=0.0, unit=SECOND)
        assert q.value == 0.0


# ── 转换 ─────────────────────────────────────────────────────────


class TestQuantityConversion:
    """单位转换测试。"""

    def test_meter_to_kilometer(self) -> None:
        """米转千米。/ Meter to kilometer."""
        q = Quantity(value=1000.0, unit=METER)
        result = q.to(KILOMETER)
        assert result.value == pytest.approx(1.0)
        assert result.unit.symbol == "km"

    def test_kilometer_to_meter(self) -> None:
        """千米转米。/ Kilometer to meter."""
        q = Quantity(value=2.5, unit=KILOMETER)
        result = q.to(METER)
        assert result.value == pytest.approx(2500.0)
        assert result.unit.symbol == "m"

    def test_centimeter_to_meter(self) -> None:
        """厘米转米。/ Centimeter to meter."""
        q = Quantity(value=150.0, unit=CENTIMETER)
        result = q.to(METER)
        assert result.value == pytest.approx(1.5)

    def test_millimeter_to_kilometer(self) -> None:
        """毫米转千米。/ Millimeter to kilometer."""
        q = Quantity(value=1_000_000.0, unit=MILLIMETER)
        result = q.to(KILOMETER)
        assert result.value == pytest.approx(1.0)

    def test_kg_to_gram(self) -> None:
        """千克转克。/ Kilogram to gram."""
        q = Quantity(value=1.0, unit=KILOGRAM)
        result = q.to(GRAM)
        assert result.value == pytest.approx(1000.0)

    def test_hour_to_second(self) -> None:
        """小时转秒。/ Hour to second."""
        q = Quantity(value=1.0, unit=HOUR)
        result = q.to(SECOND)
        assert result.value == pytest.approx(3600.0)


# ── 加法 ─────────────────────────────────────────────────────────


class TestQuantityAddition:
    """加法测试。"""

    def test_add_same_unit(self) -> None:
        """同单位相加。/ Add same-unit quantities."""
        a = Quantity(value=3.0, unit=METER)
        b = Quantity(value=5.0, unit=METER)
        result = a + b
        assert result.value == pytest.approx(8.0)
        assert result.unit.symbol == "m"

    def test_add_same_unit_zero(self) -> None:
        """同单位加零。/ Add zero same-unit."""
        a = Quantity(value=7.0, unit=METER)
        b = Quantity(value=0.0, unit=METER)
        result = a + b
        assert result.value == pytest.approx(7.0)

    def test_add_different_unit_fails(self) -> None:
        """不同单位相加失败。/ Different-unit add fails."""
        a = Quantity(value=1.0, unit=METER)
        b = Quantity(value=1.0, unit=KILOGRAM)
        with pytest.raises(TypeError, match="different units"):
            a + b  # noqa: B015

    def test_add_different_same_dim_fails(self) -> None:
        """同维度不同单位相加失败。
        Same-dimension different-unit add fails.
        """
        a = Quantity(value=1.0, unit=METER)
        b = Quantity(value=1.0, unit=KILOMETER)
        with pytest.raises(TypeError, match="different units"):
            a + b  # noqa: B015


# ── 减法 ─────────────────────────────────────────────────────────


class TestQuantitySubtraction:
    """减法测试。"""

    def test_sub_same_unit(self) -> None:
        """同单位相减。/ Subtract same-unit quantities."""
        a = Quantity(value=10.0, unit=METER)
        b = Quantity(value=3.0, unit=METER)
        result = a - b
        assert result.value == pytest.approx(7.0)

    def test_sub_different_unit_fails(self) -> None:
        """不同单位相减失败。/ Different-unit sub fails."""
        a = Quantity(value=1.0, unit=METER)
        b = Quantity(value=1.0, unit=SECOND)
        with pytest.raises(TypeError, match="different units"):
            a - b  # noqa: B015


# ── 乘除法 ───────────────────────────────────────────────────────


class TestQuantityMultiplication:
    """标量乘除法测试。"""

    def test_mul_scalar(self) -> None:
        """标量乘法。/ Scalar multiplication."""
        q = Quantity(value=5.0, unit=METER)
        result = q * 3.0
        assert result.value == pytest.approx(15.0)
        assert result.unit.symbol == "m"

    def test_mul_zero(self) -> None:
        """乘以零。/ Multiply by zero."""
        q = Quantity(value=5.0, unit=METER)
        result = q * 0.0
        assert result.value == pytest.approx(0.0)

    def test_mul_negative(self) -> None:
        """乘以负数。/ Multiply by negative."""
        q = Quantity(value=4.0, unit=METER)
        result = q * -2.0
        assert result.value == pytest.approx(-8.0)

    def test_truediv_scalar(self) -> None:
        """标量除法。/ Scalar division."""
        q = Quantity(value=20.0, unit=METER)
        result = q / 4.0
        assert result.value == pytest.approx(5.0)
        assert result.unit.symbol == "m"

    def test_truediv_negative(self) -> None:
        """负数除法。/ Negative division."""
        q = Quantity(value=10.0, unit=METER)
        result = q / -2.0
        assert result.value == pytest.approx(-5.0)


# ── 不可变性 ─────────────────────────────────────────────────────


class TestQuantityFrozen:
    """不可变性测试。"""

    def test_frozen_value(self) -> None:
        """值不可变。/ Value is frozen."""
        q = Quantity(value=1.0, unit=METER)
        with pytest.raises(AttributeError):
            q.value = 2.0  # type: ignore[misc]

    def test_frozen_unit(self) -> None:
        """单位不可变。/ Unit is frozen."""
        q = Quantity(value=1.0, unit=METER)
        with pytest.raises(AttributeError):
            q.unit = KILOGRAM  # type: ignore[misc]

    def test_equality(self) -> None:
        """相等比较。/ Equality."""
        a = Quantity(value=5.0, unit=METER)
        b = Quantity(value=5.0, unit=METER)
        assert a == b

    def test_inequality(self) -> None:
        """不等比较。/ Inequality."""
        a = Quantity(value=5.0, unit=METER)
        b = Quantity(value=3.0, unit=METER)
        assert a != b


# ── 字符串表示 ───────────────────────────────────────────────────


class TestQuantityStr:
    """字符串表示测试。"""

    def test_str_meter(self) -> None:
        """米制字符串。/ Meter string."""
        q = Quantity(value=9.8, unit=METER)
        assert str(q) == "9.8 m"

    def test_str_kg(self) -> None:
        """千克字符串。/ Kilogram string."""
        q = Quantity(value=1.0, unit=KILOGRAM)
        assert str(q) == "1.0 kg"


# ── 值域 ─────────────────────────────────────────────────────────


class TestQuantityValueRange:
    """物理量值域测试。"""

    def test_contains_inside(self) -> None:
        """范围内值。/ Value inside range."""
        lo = Quantity(value=0.0, unit=METER)
        hi = Quantity(value=100.0, unit=METER)
        rng = QuantityValueRange(min_qty=lo, max_qty=hi)
        q = Quantity(value=50.0, unit=METER)
        assert rng.contains(q)

    def test_contains_boundary(self) -> None:
        """边界值。/ Boundary value."""
        lo = Quantity(value=0.0, unit=METER)
        hi = Quantity(value=100.0, unit=METER)
        rng = QuantityValueRange(min_qty=lo, max_qty=hi)
        assert rng.contains(lo)
        assert rng.contains(hi)

    def test_contains_outside(self) -> None:
        """范围外值。/ Value outside range."""
        lo = Quantity(value=0.0, unit=METER)
        hi = Quantity(value=100.0, unit=METER)
        rng = QuantityValueRange(min_qty=lo, max_qty=hi)
        q = Quantity(value=200.0, unit=METER)
        assert not rng.contains(q)

    def test_contains_different_unit(self) -> None:
        """不同单位范围检查。/ Range check different units."""
        lo = Quantity(value=0.0, unit=METER)
        hi = Quantity(value=1.0, unit=KILOMETER)
        rng = QuantityValueRange(min_qty=lo, max_qty=hi)
        q = Quantity(value=500.0, unit=METER)
        assert rng.contains(q)


# ── 极值 ─────────────────────────────────────────────────────────


class TestMinMax:
    """极值工具测试。"""

    def test_min_quantity(self) -> None:
        """最小值。/ Minimum quantity."""
        items = [
            Quantity(value=3.0, unit=METER),
            Quantity(value=1.0, unit=METER),
            Quantity(value=2.0, unit=METER),
        ]
        result = min_quantity(items)
        assert result.value == pytest.approx(1.0)

    def test_max_quantity(self) -> None:
        """最大值。/ Maximum quantity."""
        items = [
            Quantity(value=3.0, unit=METER),
            Quantity(value=1.0, unit=METER),
            Quantity(value=2.0, unit=METER),
        ]
        result = max_quantity(items)
        assert result.value == pytest.approx(3.0)

    def test_min_single(self) -> None:
        """单元素最小值。/ Min of single item."""
        items = [Quantity(value=42.0, unit=METER)]
        assert min_quantity(items).value == pytest.approx(42.0)

    def test_max_single(self) -> None:
        """单元素最大值。/ Max of single item."""
        items = [Quantity(value=42.0, unit=METER)]
        assert max_quantity(items).value == pytest.approx(42.0)


# ── 时长扩展 ─────────────────────────────────────────────────────


class TestDurationExtensions:
    """时长扩展测试。"""

    def test_from_hours(self) -> None:
        """从小时创建。/ Create from hours."""
        q = from_hours(2.0)
        assert q.value == pytest.approx(7200.0)
        assert q.unit.symbol == "s"

    def test_from_minutes(self) -> None:
        """从分钟创建。/ Create from minutes."""
        q = from_minutes(30.0)
        assert q.value == pytest.approx(1800.0)
        assert q.unit.symbol == "s"

    def test_to_timedelta(self) -> None:
        """转 timedelta。/ Convert to timedelta."""
        q = from_hours(1.0)
        td = to_timedelta(q)
        assert td == timedelta(hours=1)

    def test_roundtrip_hours(self) -> None:
        """小时往返转换。/ Hours roundtrip."""
        q = from_hours(3.5)
        td = to_timedelta(q)
        assert td == timedelta(hours=3.5)
