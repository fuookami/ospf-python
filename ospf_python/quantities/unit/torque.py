"""力矩单位。/ Torque units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Torque:
    """力矩单位。/ Torque unit.

    SI 导出单位为牛顿米 (N⋅m)。/ SI derived unit is newton-metre (N⋅m).
    """

    _symbol: str = "N⋅m"
    _factor: float = 1.0  # 转换到 SI 单位的系数 / factor to SI

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位。/ Convert value to SI unit."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位转换值。/ Convert value from SI unit."""
        return value / self._factor


# 预定义力矩单位 / Predefined torque units
NEWTON_METRE = Torque("N⋅m", 1.0)
KILONEWTON_METRE = Torque("kN⋅m", 1_000.0)
FOOT_POUND_FORCE = Torque("ft⋅lbf", 1.3558179483314)
INCH_POUND_FORCE = Torque("in⋅lbf", 0.11298482902762)
KILOGRAM_FORCE_METRE = Torque("kgf⋅m", 9.80665)
DYNE_CENTIMETRE = Torque("dyn⋅cm", 1e-7)
