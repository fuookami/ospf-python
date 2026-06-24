"""能量单位。/ Energy units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Energy:
    """能量单位。/ Energy unit.

    SI 导出单位为焦耳 (J)。/ SI derived unit is joule (J).
    """

    _symbol: str = "J"
    _factor: float = 1.0  # 转换到 SI 单位的系数 / factor to SI

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（焦耳）。/ Convert to SI (joule)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（焦耳）转换值。/ Convert from SI (joule)."""
        return value / self._factor


# 预定义能量单位 / Predefined energy units
JOULE = Energy("J", 1.0)
KILOJOULE = Energy("kJ", 1_000.0)
MEGAJOULE = Energy("MJ", 1e6)
GIGAJOULE = Energy("GJ", 1e9)
CALORIE = Energy("cal", 4.184)
KILOCALORIE = Energy("kcal", 4_184.0)
WATT_HOUR = Energy("Wh", 3_600.0)
KILOWATT_HOUR = Energy("kWh", 3_600_000.0)
ELECTRON_VOLT = Energy("eV", 1.602176634e-19)
ERG = Energy("erg", 1e-7)
BTU = Energy("BTU", 1_055.06)
FOOT_POUND = Energy("ft-lb", 1.3558179483314)
