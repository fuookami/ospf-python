"""力单位。/ Force units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Force:
    """力单位。/ Force unit.

    SI 导出单位为牛顿 (N)。/ SI derived unit is newton (N).
    """

    _symbol: str = "N"
    _factor: float = 1.0  # 转换到 SI 单位的系数 / factor to SI

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（牛顿）。/ Convert to SI (newton)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（牛顿）转换值。/ Convert from SI (newton)."""
        return value / self._factor


# 预定义力单位 / Predefined force units
NEWTON = Force("N", 1.0)
KILONEWTON = Force("kN", 1_000.0)
MEGANEWTON = Force("MN", 1e6)
DYNE = Force("dyn", 1e-5)
POUND_FORCE = Force("lbf", 4.4482216152605)
KILOGRAM_FORCE = Force("kgf", 9.80665)
KIP = Force("kip", 4_448.2216152605)
