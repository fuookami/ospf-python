"""功率单位。/ Power units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Power:
    """功率单位。/ Power unit.

    SI 导出单位为瓦特 (W)。/ SI derived unit is watt (W).
    """

    _symbol: str = "W"
    _factor: float = 1.0  # 转换到 SI 单位的系数 / factor to SI

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（瓦特）。/ Convert to SI (watt)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（瓦特）转换值。/ Convert from SI (watt)."""
        return value / self._factor


# 预定义功率单位 / Predefined power units
WATT = Power("W", 1.0)
KILOWATT = Power("kW", 1_000.0)
MEGAWATT = Power("MW", 1e6)
GIGAWATT = Power("GW", 1e9)
MILLIWATT = Power("mW", 0.001)
HORSEPOWER = Power("hp", 745.69987158227)
HORSEPOWER_METRIC = Power("PS", 735.49875)
