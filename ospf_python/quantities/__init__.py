"""Physical quantities module.

Provides Quantity and PhysicalUnit for type-safe physical computations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique

from ospf_python.utils.error import ErrorCode
from ospf_python.utils.result import Result, failed, ok


@unique
class Dimension(Enum):
    """Physical dimension.

    物理量纲。
    """

    LENGTH = "length"
    AREA = "area"
    VOLUME = "volume"
    MASS = "mass"
    TIME = "time"
    TEMPERATURE = "temperature"
    SPEED = "speed"
    FORCE = "force"
    ENERGY = "energy"
    POWER = "power"
    PRESSURE = "pressure"
    DIMENSIONLESS = "dimensionless"


@dataclass(frozen=True, slots=True)
class PhysicalUnit:
    """Physical unit with dimension and conversion factor.

    物理单位，包含量纲和换算因子。
    """

    name: str
    symbol: str
    dimension: Dimension
    factor: float
    offset: float = 0.0

    def to_si(self, value: float) -> float:
        """Convert value to SI base unit."""
        return value * self.factor + self.offset

    def from_si(self, value: float) -> float:
        """Convert value from SI base unit."""
        return (value - self.offset) / self.factor

    def __repr__(self) -> str:
        return f"{self.name} ({self.symbol})"


# Length units
METER = PhysicalUnit("meter", "m", Dimension.LENGTH, 1.0)
KILOMETER = PhysicalUnit("kilometer", "km", Dimension.LENGTH, 1000.0)
CENTIMETER = PhysicalUnit("centimeter", "cm", Dimension.LENGTH, 0.01)
MILLIMETER = PhysicalUnit("millimeter", "mm", Dimension.LENGTH, 0.001)
INCH = PhysicalUnit("inch", "in", Dimension.LENGTH, 0.0254)
FOOT = PhysicalUnit("foot", "ft", Dimension.LENGTH, 0.3048)

# Area units
SQUARE_METER = PhysicalUnit("square_meter", "m²", Dimension.AREA, 1.0)
SQUARE_KILOMETER = PhysicalUnit("square_kilometer", "km²", Dimension.AREA, 1e6)
HECTARE = PhysicalUnit("hectare", "ha", Dimension.AREA, 1e4)

# Volume units
CUBIC_METER = PhysicalUnit("cubic_meter", "m³", Dimension.VOLUME, 1.0)
LITER = PhysicalUnit("liter", "L", Dimension.VOLUME, 0.001)
MILLILITER = PhysicalUnit("milliliter", "mL", Dimension.VOLUME, 1e-6)

# Mass units
KILOGRAM = PhysicalUnit("kilogram", "kg", Dimension.MASS, 1.0)
GRAM = PhysicalUnit("gram", "g", Dimension.MASS, 0.001)
POUND = PhysicalUnit("pound", "lb", Dimension.MASS, 0.45359237)

# Time units
SECOND = PhysicalUnit("second", "s", Dimension.TIME, 1.0)
MINUTE = PhysicalUnit("minute", "min", Dimension.TIME, 60.0)
HOUR = PhysicalUnit("hour", "h", Dimension.TIME, 3600.0)
DAY = PhysicalUnit("day", "d", Dimension.TIME, 86400.0)

# Temperature units
KELVIN = PhysicalUnit("kelvin", "K", Dimension.TEMPERATURE, 1.0)
CELSIUS = PhysicalUnit("celsius", "°C", Dimension.TEMPERATURE, 1.0, 273.15)
FAHRENHEIT = PhysicalUnit(
    "fahrenheit", "°F", Dimension.TEMPERATURE, 5.0 / 9.0, 459.67 * 5.0 / 9.0
)

# Speed units
METER_PER_SECOND = PhysicalUnit("meter_per_second", "m/s", Dimension.SPEED, 1.0)
KILOMETER_PER_HOUR = PhysicalUnit(
    "kilometer_per_hour", "km/h", Dimension.SPEED, 1.0 / 3.6
)

# Force units
NEWTON = PhysicalUnit("newton", "N", Dimension.FORCE, 1.0)
KILONEWTON = PhysicalUnit("kilonewton", "kN", Dimension.FORCE, 1000.0)

# Energy units
JOULE = PhysicalUnit("joule", "J", Dimension.ENERGY, 1.0)
KILOJOULE = PhysicalUnit("kilojoule", "kJ", Dimension.ENERGY, 1000.0)
WATT_HOUR = PhysicalUnit("watt_hour", "Wh", Dimension.ENERGY, 3600.0)
KILOWATT_HOUR = PhysicalUnit("kilowatt_hour", "kWh", Dimension.ENERGY, 3.6e6)

# Power units
WATT = PhysicalUnit("watt", "W", Dimension.POWER, 1.0)
KILOWATT = PhysicalUnit("kilowatt", "kW", Dimension.POWER, 1000.0)

# Pressure units
PASCAL = PhysicalUnit("pascal", "Pa", Dimension.PRESSURE, 1.0)
KILOPASCAL = PhysicalUnit("kilopascal", "kPa", Dimension.PRESSURE, 1000.0)
BAR = PhysicalUnit("bar", "bar", Dimension.PRESSURE, 1e5)
ATMOSPHERE = PhysicalUnit("atmosphere", "atm", Dimension.PRESSURE, 101325.0)

# Dimensionless
DIMENSIONLESS = PhysicalUnit("dimensionless", "", Dimension.DIMENSIONLESS, 1.0)


@dataclass(frozen=True, slots=True)
class Quantity:
    """Physical quantity with value and unit.

    物理量，包含值和单位。
    """

    value: float
    unit: PhysicalUnit

    def to(self, target_unit: PhysicalUnit) -> Result[Quantity]:
        """Convert to target unit."""
        if self.unit.dimension != target_unit.dimension:
            return failed(
                ErrorCode.ILLEGAL_ARGUMENT,
                f"Cannot convert from {self.unit.dimension.value} to {target_unit.dimension.value}",
            )
        si_value = self.unit.to_si(self.value)
        new_value = target_unit.from_si(si_value)
        return ok(Quantity(new_value, target_unit))

    def __add__(self, other: Quantity) -> Result[Quantity]:
        """Add quantities."""
        if self.unit.dimension != other.unit.dimension:
            return failed(
                ErrorCode.ILLEGAL_ARGUMENT,
                f"Cannot add {self.unit.dimension.value} and {other.unit.dimension.value}",
            )
        other_si = other.unit.to_si(other.value)
        self_si = self.unit.to_si(self.value)
        result_si = self_si + other_si
        result_value = self.unit.from_si(result_si)
        return ok(Quantity(result_value, self.unit))

    def __sub__(self, other: Quantity) -> Result[Quantity]:
        """Subtract quantities."""
        if self.unit.dimension != other.unit.dimension:
            return failed(
                ErrorCode.ILLEGAL_ARGUMENT,
                f"Cannot subtract {other.unit.dimension.value} from {self.unit.dimension.value}",
            )
        other_si = other.unit.to_si(other.value)
        self_si = self.unit.to_si(self.value)
        result_si = self_si - other_si
        result_value = self.unit.from_si(result_si)
        return ok(Quantity(result_value, self.unit))

    def __mul__(self, scalar: float) -> Quantity:
        """Multiply by scalar."""
        return Quantity(self.value * scalar, self.unit)

    def __rmul__(self, scalar: float) -> Quantity:
        """Reverse multiply by scalar."""
        return Quantity(self.value * scalar, self.unit)

    def __truediv__(self, scalar: float) -> Quantity:
        """Divide by scalar."""
        return Quantity(self.value / scalar, self.unit)

    def __neg__(self) -> Quantity:
        """Negate quantity."""
        return Quantity(-self.value, self.unit)

    def __abs__(self) -> Quantity:
        """Absolute value."""
        return Quantity(abs(self.value), self.unit)

    def __lt__(self, other: Quantity) -> bool:
        """Less than comparison."""
        if self.unit.dimension != other.unit.dimension:
            raise ValueError(
                f"Cannot compare {self.unit.dimension.value} and {other.unit.dimension.value}"
            )
        return self.unit.to_si(self.value) < other.unit.to_si(other.value)

    def __le__(self, other: Quantity) -> bool:
        """Less than or equal comparison."""
        if self.unit.dimension != other.unit.dimension:
            raise ValueError("Cannot compare dimensions")
        return self.unit.to_si(self.value) <= other.unit.to_si(other.value)

    def __gt__(self, other: Quantity) -> bool:
        """Greater than comparison."""
        if self.unit.dimension != other.unit.dimension:
            raise ValueError("Cannot compare dimensions")
        return self.unit.to_si(self.value) > other.unit.to_si(other.value)

    def __ge__(self, other: Quantity) -> bool:
        """Greater than or equal comparison."""
        if self.unit.dimension != other.unit.dimension:
            raise ValueError("Cannot compare dimensions")
        return self.unit.to_si(self.value) >= other.unit.to_si(other.value)

    def __eq__(self, other: object) -> bool:
        """Equality comparison."""
        if not isinstance(other, Quantity):
            return NotImplemented
        if self.unit.dimension != other.unit.dimension:
            return False
        return abs(self.unit.to_si(self.value) - other.unit.to_si(other.value)) < 1e-10

    def __hash__(self) -> int:
        """Hash."""
        return hash((self.unit.dimension, self.unit.to_si(self.value)))

    def __repr__(self) -> str:
        return f"{self.value} {self.unit.symbol}"


# Convenience constructors
def meters(value: float) -> Quantity:
    return Quantity(value, METER)


def kilometers(value: float) -> Quantity:
    return Quantity(value, KILOMETER)


def centimeters(value: float) -> Quantity:
    return Quantity(value, CENTIMETER)


def kilograms(value: float) -> Quantity:
    return Quantity(value, KILOGRAM)


def grams(value: float) -> Quantity:
    return Quantity(value, GRAM)


def seconds(value: float) -> Quantity:
    return Quantity(value, SECOND)


def minutes(value: float) -> Quantity:
    return Quantity(value, MINUTE)


def hours(value: float) -> Quantity:
    return Quantity(value, HOUR)


def celsius(value: float) -> Quantity:
    return Quantity(value, CELSIUS)


def kelvin(value: float) -> Quantity:
    return Quantity(value, KELVIN)


def newtons(value: float) -> Quantity:
    return Quantity(value, NEWTON)


def joules(value: float) -> Quantity:
    return Quantity(value, JOULE)


def watts(value: float) -> Quantity:
    return Quantity(value, WATT)


def pascals(value: float) -> Quantity:
    return Quantity(value, PASCAL)
