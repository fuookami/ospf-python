"""电流单位。/ Electric current units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Current:
    """电流单位。/ Electric current unit.

    SI 基本单位为安培 (A)。/ SI base unit is ampere (A).
    """

    _symbol: str = "A"
    _factor: float = 1.0  # 转换到 SI 基本单位的系数 / factor to SI base

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（安培）。/ Convert value to SI (ampere)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（安培）转换值。/ Convert value from SI (ampere)."""
        return value / self._factor


# 预定义电流单位 / Predefined current units
AMPERE = Current("A", 1.0)
MILLIAMPERE = Current("mA", 0.001)
MICROAMPERE = Current("uA", 1e-6)
KILOAMPERE = Current("kA", 1_000.0)
