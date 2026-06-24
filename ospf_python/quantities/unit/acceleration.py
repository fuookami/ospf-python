"""加速度单位。/ Acceleration units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Acceleration:
    """加速度单位。/ Acceleration unit.

    SI 导出单位为米每二次方秒 (m/s^2)。/
    SI derived unit is metre/second^2 (m/s^2).
    """

    _symbol: str = "m/s^2"
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


# 预定义加速度单位 / Predefined acceleration units
METRE_PER_SQ_SECOND = Acceleration("m/s^2", 1.0)
KILOMETRE_PER_SQ_HOUR = Acceleration("km/h^2", 1.0 / 12_960_000.0)
GRAVITY_STANDARD = Acceleration("g", 9.80665)
FOOT_PER_SQ_SECOND = Acceleration("ft/s^2", 0.3048)
GAL = Acceleration("Gal", 0.01)
