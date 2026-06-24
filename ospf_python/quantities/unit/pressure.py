"""压强单位。/ Pressure units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pressure:
    """压强单位。/ Pressure unit.

    SI 导出单位为帕斯卡 (Pa)。/ SI derived unit is pascal (Pa).
    """

    _symbol: str = "Pa"
    _factor: float = 1.0  # 转换到 SI 单位的系数 / factor to SI

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（帕斯卡）。/ Convert to SI (pascal)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（帕斯卡）转换值。/ Convert from SI (pascal)."""
        return value / self._factor


# 预定义压强单位 / Predefined pressure units
PASCAL = Pressure("Pa", 1.0)
KILOPASCAL = Pressure("kPa", 1_000.0)
MEGAPASCAL = Pressure("MPa", 1e6)
GIGAPASCAL = Pressure("GPa", 1e9)
BAR = Pressure("bar", 1e5)
MILLIBAR = Pressure("mbar", 100.0)
ATMOSPHERE = Pressure("atm", 101_325.0)
TORR = Pressure("Torr", 133.32236842105)
PSI = Pressure("psi", 6_894.757293168)
MMHG = Pressure("mmHg", 133.32236842105)
