"""发光强度单位。/ Luminous intensity units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LuminousIntensity:
    """发光强度单位。/ Luminous intensity unit.

    SI 基本单位为坎德拉 (cd)。/ SI base unit is candela (cd).
    """

    _symbol: str = "cd"
    _factor: float = 1.0  # 转换到 SI 基本单位的系数 / factor to SI base

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（坎德拉）。/ Convert value to SI (candela)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（坎德拉）转换值。/ Convert value from SI (candela)."""
        return value / self._factor


# 预定义发光强度单位 / Predefined luminous intensity units
CANDELA = LuminousIntensity("cd", 1.0)
MILLICANDELA = LuminousIntensity("mcd", 0.001)
Kilocandela = LuminousIntensity("kcd", 1_000.0)
