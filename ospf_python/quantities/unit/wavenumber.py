"""波数单位。/ Wavenumber units."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Wavenumber:
    """波数单位。/ Wavenumber unit.

    SI 导出单位为每米 (1/m)。/ SI derived unit is 1/metre (1/m).
    """

    _symbol: str = "1/m"
    _factor: float = 1.0  # 转换到 SI 单位的系数 / factor to SI

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（每米）。/ Convert to SI (1/metre)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（每米）转换值。/ Convert from SI (1/metre)."""
        return value / self._factor


# 预定义波数单位 / Predefined wavenumber units
RECIPROCAL_METRE = Wavenumber("1/m", 1.0)
RECIPROCAL_CENTIMETRE = Wavenumber("1/cm", 100.0)
RECIPROCAL_MILLIMETRE = Wavenumber("1/mm", 1_000.0)
RECIPROCAL_KILOMETRE = Wavenumber("1/km", 0.001)
RADIAN_PER_METRE = Wavenumber("rad/m", 1.0)
CYCLE_PER_METRE = Wavenumber("cyc/m", 2.0 * math.pi)
