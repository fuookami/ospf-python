"""质量单位。/ Mass units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Mass:
    """质量单位。/ Mass unit.

    SI 基本单位为千克 (kg)。/ SI base unit is kilogram (kg).
    """

    _symbol: str = "kg"
    _factor: float = 1.0  # 转换到 SI 基本单位的系数 / factor to SI base

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（千克）。/ Convert value to SI (kilogram)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（千克）转换值。/ Convert value from SI (kilogram)."""
        return value / self._factor


# 预定义质量单位 / Predefined mass units
KILOGRAM = Mass("kg", 1.0)
GRAM = Mass("g", 0.001)
MILLIGRAM = Mass("mg", 1e-6)
MICROGRAM = Mass("ug", 1e-9)
METRIC_TON = Mass("t", 1_000.0)
OUNCE = Mass("oz", 0.028349523125)
POUND = Mass("lb", 0.45359237)
SHORT_TON = Mass("ton", 907.18474)
LONG_TON = Mass("lton", 1_016.0469088)
ATOMIC_MASS_UNIT = Mass("u", 1.66053906660e-27)
