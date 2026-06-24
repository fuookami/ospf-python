"""体积单位。/ Volume units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Volume:
    """体积单位。/ Volume unit.

    SI 导出单位为立方米 (m^3)。/ SI derived unit is cubic metre (m^3).
    """

    _symbol: str = "m^3"
    _factor: float = 1.0  # 转换到 SI 单位的系数 / factor to SI

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（立方米）。/ Convert to SI (cubic metre)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（立方米）转换值。/ Convert from SI (cubic metre)."""
        return value / self._factor


# 预定义体积单位 / Predefined volume units
CUBIC_METER = Volume("m^3", 1.0)
LITER = Volume("L", 0.001)
MILLILITER = Volume("mL", 1e-6)
CUBIC_CENTIMETER = Volume("cm^3", 1e-6)
CUBIC_KILOMETER = Volume("km^3", 1e9)
CUBIC_FOOT = Volume("ft^3", 0.028316846592)
CUBIC_INCH = Volume("in^3", 1.6387064e-5)
GALLON_US = Volume("gal", 3.785411784e-3)
GALLON_UK = Volume("gal_uk", 4.54609e-3)
BARREL = Volume("bbl", 0.158987294928)
