"""温度单位。/ Temperature units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Temperature:
    """温度单位。/ Temperature unit.

    SI 基本单位为开尔文 (K)。/ SI base unit is kelvin (K).
    注意：开尔文与摄氏度之间存在偏移量。/
    Note: offset exists between kelvin and Celsius.
    """

    _symbol: str = "K"
    _factor: float = 1.0  # 缩放系数 / scale factor
    _offset: float = 0.0  # 偏移量 / offset

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（开尔文）。/ Convert value to SI (kelvin)."""
        return value * self._factor + self._offset

    def from_si(self, value: float) -> float:
        """从 SI 单位（开尔文）转换值。/ Convert value from SI (kelvin)."""
        return (value - self._offset) / self._factor


# 预定义温度单位 / Predefined temperature units
KELVIN = Temperature("K", 1.0, 0.0)
CELSIUS = Temperature("C", 1.0, 273.15)
FAHRENHEIT = Temperature("F", 5.0 / 9.0, 255.3722222222222)
RANKINE = Temperature("R", 5.0 / 9.0, 0.0)
