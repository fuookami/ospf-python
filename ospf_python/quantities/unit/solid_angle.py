"""立体角单位。/ Solid angle units."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SolidAngle:
    """立体角单位。/ Solid angle unit.

    SI 导出单位为球面度 (sr)。/ SI derived unit is steradian (sr).
    """

    _symbol: str = "sr"
    _factor: float = 1.0  # 转换到 SI 单位的系数 / factor to SI

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（球面度）。/ Convert to SI (steradian)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（球面度）转换值。/ Convert from SI (steradian)."""
        return value / self._factor


# 预定义立体角单位 / Predefined solid angle units
STERADIAN = SolidAngle("sr", 1.0)
SQUARE_DEGREE = SolidAngle("deg^2", (math.pi / 180.0) ** 2)
SPHERE = SolidAngle("sphere", 4.0 * math.pi)
