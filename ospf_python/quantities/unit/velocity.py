"""速度单位。/ Velocity units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Velocity:
    """速度单位。/ Velocity unit.

    SI 导出单位为米每秒 (m/s)。/ SI derived unit is metre/second (m/s).
    """

    _symbol: str = "m/s"
    _factor: float = 1.0  # 转换到 SI 单位的系数 / factor to SI

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（米每秒）。/ Convert to SI (m/s)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（米每秒）转换值。/ Convert from SI (m/s)."""
        return value / self._factor


# 预定义速度单位 / Predefined velocity units
METRE_PER_SECOND = Velocity("m/s", 1.0)
KILOMETRE_PER_HOUR = Velocity("km/h", 1.0 / 3.6)
MILE_PER_HOUR = Velocity("mph", 0.44704)
KNOT = Velocity("kn", 0.514444)
FOOT_PER_SECOND = Velocity("ft/s", 0.3048)
SPEED_OF_LIGHT = Velocity("c", 299_792_458.0)
