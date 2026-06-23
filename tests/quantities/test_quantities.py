"""Tests for ospf_python.quantities module."""

import pytest

from ospf_python.quantities import (
    CELSIUS,
    CENTIMETER,
    KELVIN,
    KILOGRAM,
    KILOMETER,
    METER,
    Quantity,
    celsius,
    centimeters,
    kelvin,
    kilograms,
    kilometers,
    meters,
)
from ospf_python.utils.result import Failed, Ok


class TestPhysicalUnit:
    """Tests for PhysicalUnit."""

    def test_creation(self) -> None:
        """Test creating unit."""
        assert METER.name == "meter"
        assert METER.symbol == "m"

    def test_to_si(self) -> None:
        """Test conversion to SI."""
        assert METER.to_si(1000.0) == 1000.0
        assert KILOMETER.to_si(1.0) == 1000.0
        assert CENTIMETER.to_si(100.0) == 1.0

    def test_from_si(self) -> None:
        """Test conversion from SI."""
        assert METER.from_si(1000.0) == 1000.0
        assert KILOMETER.from_si(1000.0) == 1.0
        assert CENTIMETER.from_si(1.0) == 100.0


class TestQuantityCreation:
    """Tests for Quantity creation."""

    def test_creation(self) -> None:
        """Test creating quantity."""
        q = Quantity(100.0, METER)
        assert q.value == 100.0
        assert q.unit == METER

    def test_convenience_constructors(self) -> None:
        """Test convenience constructors."""
        assert meters(100.0).unit == METER
        assert kilometers(1.0).unit == KILOMETER
        assert kilograms(5.0).unit == KILOGRAM


class TestQuantityConversion:
    """Tests for unit conversion."""

    def test_convert_length(self) -> None:
        """Test length conversion."""
        q = meters(1000.0)
        result = q.to(KILOMETER)
        assert isinstance(result, Ok)
        assert abs(result.value.value - 1.0) < 1e-10

    def test_convert_m_to_cm(self) -> None:
        """Test m to cm conversion."""
        q = meters(1.0)
        result = q.to(CENTIMETER)
        assert isinstance(result, Ok)
        assert abs(result.value.value - 100.0) < 1e-10

    def test_convert_incompatible(self) -> None:
        """Test incompatible conversion."""
        q = meters(1.0)
        result = q.to(KILOGRAM)
        assert isinstance(result, Failed)


class TestQuantityArithmetic:
    """Tests for quantity arithmetic."""

    def test_add_same_unit(self) -> None:
        """Test adding same units."""
        q1 = meters(1.0)
        q2 = meters(2.0)
        result = q1 + q2
        assert isinstance(result, Ok)
        assert abs(result.value.value - 3.0) < 1e-10

    def test_add_different_units_same_dimension(self) -> None:
        """Test adding different units same dimension."""
        q1 = meters(1.0)
        q2 = centimeters(100.0)
        result = q1 + q2
        assert isinstance(result, Ok)
        assert abs(result.value.value - 2.0) < 1e-10

    def test_add_different_dimensions(self) -> None:
        """Test adding different dimensions."""
        q1 = meters(1.0)
        q2 = kilograms(1.0)
        result = q1 + q2
        assert isinstance(result, Failed)

    def test_sub_same_unit(self) -> None:
        """Test subtracting same units."""
        q1 = meters(3.0)
        q2 = meters(1.0)
        result = q1 - q2
        assert isinstance(result, Ok)
        assert abs(result.value.value - 2.0) < 1e-10

    def test_sub_different_dimensions(self) -> None:
        """Test subtracting different dimensions."""
        q1 = meters(1.0)
        q2 = kilograms(1.0)
        result = q1 - q2
        assert isinstance(result, Failed)

    def test_mul_scalar(self) -> None:
        """Test multiplying by scalar."""
        q = meters(2.0)
        result = q * 3.0
        assert result.value == 6.0

    def test_rmul_scalar(self) -> None:
        """Test reverse multiplying by scalar."""
        q = meters(2.0)
        result = 3.0 * q
        assert result.value == 6.0

    def test_div_scalar(self) -> None:
        """Test dividing by scalar."""
        q = meters(6.0)
        result = q / 2.0
        assert result.value == 3.0

    def test_neg(self) -> None:
        """Test negation."""
        q = meters(5.0)
        result = -q
        assert result.value == -5.0

    def test_abs(self) -> None:
        """Test absolute value."""
        q = meters(-5.0)
        result = abs(q)
        assert result.value == 5.0


class TestQuantityComparison:
    """Tests for quantity comparison."""

    def test_lt(self) -> None:
        """Test less than."""
        q1 = meters(1.0)
        q2 = meters(2.0)
        assert q1 < q2

    def test_le(self) -> None:
        """Test less than or equal."""
        q1 = meters(1.0)
        q2 = meters(1.0)
        assert q1 <= q2

    def test_gt(self) -> None:
        """Test greater than."""
        q1 = meters(2.0)
        q2 = meters(1.0)
        assert q1 > q2

    def test_ge(self) -> None:
        """Test greater than or equal."""
        q1 = meters(1.0)
        q2 = meters(1.0)
        assert q1 >= q2

    def test_eq(self) -> None:
        """Test equality."""
        q1 = meters(1.0)
        q2 = meters(1.0)
        assert q1 == q2

    def test_eq_different_units(self) -> None:
        """Test equality with different units."""
        q1 = meters(1.0)
        q2 = centimeters(100.0)
        assert q1 == q2

    def test_compare_different_dimensions_raises(self) -> None:
        """Test comparing different dimensions raises."""
        q1 = meters(1.0)
        q2 = kilograms(1.0)
        with pytest.raises(ValueError):
            _ = q1 < q2


class TestTemperature:
    """Tests for temperature conversions."""

    def test_celsius_to_kelvin(self) -> None:
        """Test Celsius to Kelvin conversion."""
        q = celsius(0.0)
        result = q.to(KELVIN)
        assert isinstance(result, Ok)
        assert abs(result.value.value - 273.15) < 1e-10

    def test_kelvin_to_celsius(self) -> None:
        """Test Kelvin to Celsius conversion."""
        q = kelvin(273.15)
        result = q.to(CELSIUS)
        assert isinstance(result, Ok)
        assert abs(result.value.value - 0.0) < 1e-10


class TestRepr:
    """Tests for string representation."""

    def test_repr(self) -> None:
        """Test repr."""
        q = meters(100.0)
        assert "100.0" in repr(q)
        assert "m" in repr(q)


class TestUnitMismatchInterception:
    """Tests for unit mismatch interception."""

    def test_add_m_and_kg_returns_failed(self) -> None:
        """Test adding meters and kilograms returns Failed."""
        q1 = meters(1.0)
        q2 = kilograms(1.0)
        result = q1 + q2
        assert isinstance(result, Failed)
        assert "Cannot add" in result.error.message

    def test_sub_m_and_kg_returns_failed(self) -> None:
        """Test subtracting meters and kilograms returns Failed."""
        q1 = meters(1.0)
        q2 = kilograms(1.0)
        result = q1 - q2
        assert isinstance(result, Failed)
        assert "Cannot subtract" in result.error.message

    def test_convert_m_to_kg_returns_failed(self) -> None:
        """Test converting meters to kilograms returns Failed."""
        q = meters(1.0)
        result = q.to(KILOGRAM)
        assert isinstance(result, Failed)
        assert "Cannot convert" in result.error.message
