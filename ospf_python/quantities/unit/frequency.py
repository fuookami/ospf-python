"""频率单位。/ Frequency units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Frequency:
    """频率单位。/ Frequency unit.

    SI 导出单位为赫兹 (Hz)。/ SI derived unit is hertz (Hz).
    """

    _symbol: str = "Hz"
    _factor: float = 1.0  # 转换到 SI 单位的系数 / factor to SI

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（赫兹）。/ Convert to SI (hertz)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（赫兹）转换值。/ Convert from SI (hertz)."""
        return value / self._factor


# 预定义频率单位 / Predefined frequency units
HERTZ = Frequency("Hz", 1.0)
KILOHERTZ = Frequency("kHz", 1_000.0)
MEGAHERTZ = Frequency("MHz", 1e6)
GIGAHERTZ = Frequency("GHz", 1e9)
TERAHERTZ = Frequency("THz", 1e12)
MILLIHERTZ = Frequency("mHz", 0.001)
REVOLUTIONS_PER_MINUTE = Frequency("rpm", 1.0 / 60.0)
