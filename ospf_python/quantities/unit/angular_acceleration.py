"""角加速度单位。/ Angular acceleration units."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class AngularAcceleration:
    """角加速度单位。/ Angular acceleration unit.

    SI 导出单位为弧度每二次方秒 (rad/s^2)。/
    SI derived unit is radian/second^2 (rad/s^2).
    """

    _symbol: str = "rad/s^2"
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


# 预定义角加速度单位 / Predefined angular acceleration units
RADIAN_PER_SQ_SECOND = AngularAcceleration("rad/s^2", 1.0)
DEGREE_PER_SQ_SECOND = AngularAcceleration("deg/s^2", math.pi / 180.0)
REVOLUTION_PER_SQ_SECOND = AngularAcceleration("rev/s^2", 2.0 * math.pi)
