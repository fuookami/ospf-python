"""角速度单位。/ Angular velocity units."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class AngularVelocity:
    """角速度单位。/ Angular velocity unit.

    SI 导出单位为弧度每秒 (rad/s)。/
    SI derived unit is radian/second (rad/s).
    """

    _symbol: str = "rad/s"
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


# 预定义角速度单位 / Predefined angular velocity units
RADIAN_PER_SECOND = AngularVelocity("rad/s", 1.0)
DEGREE_PER_SECOND = AngularVelocity("deg/s", math.pi / 180.0)
REVOLUTION_PER_SECOND = AngularVelocity("rev/s", 2.0 * math.pi)
REVOLUTION_PER_MINUTE = AngularVelocity("rpm", 2.0 * math.pi / 60.0)
