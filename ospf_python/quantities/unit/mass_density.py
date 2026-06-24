"""密度单位。/ Mass density units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MassDensity:
    """密度单位。/ Mass density unit.

    SI 导出单位为千克每立方米 (kg/m^3)。/
    SI derived unit is kilogram/cubic metre (kg/m^3).
    """

    _symbol: str = "kg/m^3"
    _factor: float = 1.0  # 转换到 SI 单位的系数 / factor to SI

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位。/ Convert value to SI unit."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位转换值。/ Convert value from SI unit."""
        return value / self._factor


# 预定义密度单位 / Predefined mass density units
KILOGRAM_PER_CUBIC_METRE = MassDensity("kg/m^3", 1.0)
GRAM_PER_CUBIC_CENTIMETRE = MassDensity("g/cm^3", 1_000.0)
KILOGRAM_PER_LITRE = MassDensity("kg/L", 1_000.0)
GRAM_PER_LITRE = MassDensity("g/L", 1.0)
POUND_PER_CUBIC_FOOT = MassDensity("lb/ft^3", 16.01846337396)
POUND_PER_CUBIC_INCH = MassDensity("lb/in^3", 27_679.904710203)
POUND_PER_GALLON = MassDensity("lb/gal", 119.8264273169)
SLUG_PER_CUBIC_FOOT = MassDensity("slug/ft^3", 515.379)
