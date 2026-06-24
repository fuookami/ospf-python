"""电阻单位。/ Electrical resistance units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Resistance:
    """电阻单位。/ Electrical resistance unit.

    SI 导出单位为欧姆 (Ω)。/ SI derived unit is ohm (Ω).
    """

    _symbol: str = "Ω"
    _factor: float = 1.0  # 转换到 SI 单位的系数 / factor to SI

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（欧姆）。/ Convert to SI (ohm)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（欧姆）转换值。/ Convert from SI (ohm)."""
        return value / self._factor


# 预定义电阻单位 / Predefined resistance units
OHM = Resistance("Ω", 1.0)
MILLIOHM = Resistance("mΩ", 0.001)
KILOOHM = Resistance("kΩ", 1_000.0)
MEGAOHM = Resistance("MΩ", 1e6)
GIGAOHM = Resistance("GΩ", 1e9)
MICROOHM = Resistance("uΩ", 1e-6)
