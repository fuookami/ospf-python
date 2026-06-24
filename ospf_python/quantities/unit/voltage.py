"""电压单位。/ Voltage units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Voltage:
    """电压单位。/ Voltage unit.

    SI 导出单位为伏特 (V)。/ SI derived unit is volt (V).
    """

    _symbol: str = "V"
    _factor: float = 1.0  # 转换到 SI 单位的系数 / factor to SI

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（伏特）。/ Convert to SI (volt)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（伏特）转换值。/ Convert from SI (volt)."""
        return value / self._factor


# 预定义电压单位 / Predefined voltage units
VOLT = Voltage("V", 1.0)
MILLIVOLT = Voltage("mV", 0.001)
MICROVOLT = Voltage("uV", 1e-6)
KILOVOLT = Voltage("kV", 1_000.0)
MEGAVOLT = Voltage("MV", 1e6)
