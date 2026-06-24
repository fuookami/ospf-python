"""信息量单位。/ Information units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Information:
    """信息量单位。/ Information unit.

    基本单位为比特 (bit)。/ Base unit is bit.
    """

    _symbol: str = "bit"
    _factor: float = 1.0  # 转换到基本单位的系数 / factor to base

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为基本单位（比特）。/ Convert to base (bit)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从基本单位（比特）转换值。/ Convert from base (bit)."""
        return value / self._factor


# 预定义信息量单位 / Predefined information units
BIT = Information("bit", 1.0)
BYTE = Information("B", 8.0)
KILOBIT = Information("kb", 1_000.0)
MEGABIT = Information("Mb", 1e6)
GIGABIT = Information("Gb", 1e9)
TERABIT = Information("Tb", 1e12)
KILOBYTE = Information("KB", 8_000.0)
MEGABYTE = Information("MB", 8e6)
GIGABYTE = Information("GB", 8e9)
TERABYTE = Information("TB", 8e12)
KIBIBYTE = Information("KiB", 8 * 1_024.0)
MEBIBYTE = Information("MiB", 8 * 1_048_576.0)
GIBIBYTE = Information("GiB", 8 * 1_073_741_824.0)
