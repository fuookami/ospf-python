"""平面角单位。/ Plane angle units."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PlaneAngle:
    """平面角单位。/ Plane angle unit.

    SI 导出单位为弧度 (rad)。/ SI derived unit is radian (rad).
    """

    _symbol: str = "rad"
    _factor: float = 1.0  # 转换到 SI 单位的系数 / factor to SI

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（弧度）。/ Convert to SI (radian)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（弧度）转换值。/ Convert from SI (radian)."""
        return value / self._factor


# 预定义平面角单位 / Predefined plane angle units
RADIAN = PlaneAngle("rad", 1.0)
DEGREE = PlaneAngle("deg", math.pi / 180.0)
ARC_MINUTE = PlaneAngle("arcmin", math.pi / 10_800.0)
ARC_SECOND = PlaneAngle("arcsec", math.pi / 648_000.0)
GRADIAN = PlaneAngle("grad", math.pi / 200.0)
REVOLUTION = PlaneAngle("rev", 2.0 * math.pi)
MILLIRADIAN = PlaneAngle("mrad", 0.001)
