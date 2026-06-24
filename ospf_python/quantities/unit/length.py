"""长度单位。/ Length units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Length:
    """长度单位。/ Length unit.

    SI 基本单位为米 (m)。/ SI base unit is metre (m).
    """

    _symbol: str = "m"
    _factor: float = 1.0  # 转换到 SI 基本单位的系数 / factor to SI base

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（米）。/ Convert value to SI (metre)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（米）转换值。/ Convert value from SI (metre)."""
        return value / self._factor


# 预定义长度单位 / Predefined length units
METER = Length("m", 1.0)
KILOMETER = Length("km", 1_000.0)
CENTIMETER = Length("cm", 0.01)
MILLIMETER = Length("mm", 0.001)
MICROMETER = Length("um", 1e-6)
NANOMETER = Length("nm", 1e-9)
INCH = Length("in", 0.0254)
FOOT = Length("ft", 0.3048)
YARD = Length("yd", 0.9144)
MILE = Length("mi", 1_609.344)
NAUTICAL_MILE = Length("nmi", 1_852.0)
ANGSTROM = Length("A", 1e-10)
