"""物质的量单位。/ Amount of substance units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Amount:
    """物质的量单位。/ Amount of substance unit.

    SI 基本单位为摩尔 (mol)。/ SI base unit is mole (mol).
    """

    _symbol: str = "mol"
    _factor: float = 1.0  # 转换到 SI 基本单位的系数 / factor to SI base

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（摩尔）。/ Convert value to SI (mole)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（摩尔）转换值。/ Convert value from SI (mole)."""
        return value / self._factor


# 预定义物质的量单位 / Predefined amount units
MOLE = Amount("mol", 1.0)
MILLIMOLE = Amount("mmol", 0.001)
MICROMOLE = Amount("umol", 1e-6)
NANOMOLE = Amount("nmol", 1e-9)
KILOMOLE = Amount("kmol", 1_000.0)
