"""流量单位。/ Flow rate units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FlowRate:
    """流量单位。/ Flow rate unit.

    SI 导出单位为立方米每秒 (m^3/s)。/
    SI derived unit is cubic metre/second (m^3/s).
    """

    _symbol: str = "m^3/s"
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


# 预定义流量单位 / Predefined flow rate units
CUBIC_METRE_PER_SECOND = FlowRate("m^3/s", 1.0)
LITRE_PER_SECOND = FlowRate("L/s", 0.001)
LITRE_PER_MINUTE = FlowRate("L/min", 1.0 / 60_000.0)
CUBIC_FOOT_PER_SECOND = FlowRate("ft^3/s", 0.028316846592)
CUBIC_FOOT_PER_MINUTE = FlowRate("ft^3/min", 0.0004719474432)
GALLON_PER_MINUTE = FlowRate("gal/min", 6.30902e-5)
