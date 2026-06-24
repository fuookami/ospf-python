"""面密度单位。/ Surface density units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SurfaceDensity:
    """面密度单位。/ Surface density unit.

    SI 导出单位为千克每平方米 (kg/m^2)。/
    SI derived unit is kilogram/square metre (kg/m^2).
    """

    _symbol: str = "kg/m^2"
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


# 预定义面密度单位 / Predefined surface density units
KILOGRAM_PER_SQUARE_METRE = SurfaceDensity("kg/m^2", 1.0)
GRAM_PER_SQUARE_CENTIMETRE = SurfaceDensity("g/cm^2", 10.0)
POUND_PER_SQUARE_FOOT = SurfaceDensity("lb/ft^2", 4.88242763638)
OUNCE_PER_SQUARE_FOOT = SurfaceDensity("oz/ft^2", 0.30515172727)
