"""面积单位。/ Area units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Area:
    """面积单位。/ Area unit.

    SI 导出单位为平方米 (m^2)。/ SI derived unit is square metre (m^2).
    """

    _symbol: str = "m^2"
    _factor: float = 1.0  # 转换到 SI 单位的系数 / factor to SI

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（平方米）。/ Convert to SI (sq metre)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（平方米）转换值。/ Convert from SI (sq metre)."""
        return value / self._factor


# 预定义面积单位 / Predefined area units
SQUARE_METER = Area("m^2", 1.0)
SQUARE_KILOMETER = Area("km^2", 1e6)
SQUARE_CENTIMETER = Area("cm^2", 1e-4)
SQUARE_MILLIMETER = Area("mm^2", 1e-6)
HECTARE = Area("ha", 1e4)
SQUARE_FOOT = Area("ft^2", 0.09290304)
SQUARE_INCH = Area("in^2", 6.4516e-4)
SQUARE_YARD = Area("yd^2", 0.83612736)
SQUARE_MILE = Area("mi^2", 2_589_988.110336)
ACRE = Area("ac", 4_046.8564224)
