"""动量单位。/ Momentum units."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python._binding.unit_registry import (
    register_unit_family as _register_unit_family,
)


@_register_unit_family(powers=(1, 1, -1, 0, 0, 0, 0, 0, 0, 0))
@dataclass(frozen=True)
class Momentum:
    """动量单位。/ Momentum unit.

    SI 导出单位为千克米每秒 (kg⋅m/s)。/
    SI derived unit is kilogram-metre/second (kg⋅m/s).
    """

    _symbol: str = "kg⋅m/s"
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


# 预定义动量单位 / Predefined momentum units
KILOGRAM_METRE_PER_SECOND = Momentum("kg⋅m/s", 1.0)
GRAM_CENTIMETRE_PER_SECOND = Momentum("g⋅cm/s", 1e-5)
POUND_FOOT_PER_SECOND = Momentum("lb⋅ft/s", 0.138254954376)
NEWTON_SECOND = Momentum("N⋅s", 1.0)
