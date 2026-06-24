"""应力单位。/ Stress units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Stress:
    """应力单位。/ Stress unit.

    SI 导出单位为帕斯卡 (Pa)。/ SI derived unit is pascal (Pa).
    与压强具有相同的量纲。/ Same dimension as pressure.
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


# 预定义应力单位 / Predefined stress units
PASCAL = Stress("Pa", 1.0)
KILOPASCAL = Stress("kPa", 1_000.0)
MEGAPASCAL = Stress("MPa", 1e6)
GIGAPASCAL = Stress("GPa", 1e9)
PSI = Stress("psi", 6_894.757293168)
KILOSI = Stress("ksi", 6_894_757.293168)
