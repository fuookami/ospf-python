"""催化活性单位。/ Catalytic activity units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalyticActivity:
    """催化活性单位。/ Catalytic activity unit.

    SI 导出单位为开特 (kat)。/ SI derived unit is katal (kat).
    """

    _symbol: str = "kat"
    _factor: float = 1.0  # 转换到 SI 单位的系数 / factor to SI

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（开特）。/ Convert to SI (katal)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（开特）转换值。/ Convert from SI (katal)."""
        return value / self._factor


# 预定义催化活性单位 / Predefined catalytic activity units
KATAL = CatalyticActivity("kat", 1.0)
MILLIKATAL = CatalyticActivity("mkat", 0.001)
MICROKATAL = CatalyticActivity("ukat", 1e-6)
NANOKATAL = CatalyticActivity("nkat", 1e-9)
PICOKATAL = CatalyticActivity("pkat", 1e-12)
UNIT = CatalyticActivity("U", 1.0 / 60e6)  # 酶单位 / enzyme unit
