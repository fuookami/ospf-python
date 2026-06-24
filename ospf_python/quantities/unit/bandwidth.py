"""带宽单位。/ Bandwidth units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Bandwidth:
    """带宽单位。/ Bandwidth unit.

    SI 导出单位为比特每秒 (bit/s)。/
    SI derived unit is bit/second (bit/s).
    """

    _symbol: str = "bit/s"
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


# 预定义带宽单位 / Predefined bandwidth units
BIT_PER_SECOND = Bandwidth("bit/s", 1.0)
KILOBIT_PER_SECOND = Bandwidth("kbit/s", 1_000.0)
MEGABIT_PER_SECOND = Bandwidth("Mbit/s", 1e6)
GIGABIT_PER_SECOND = Bandwidth("Gbit/s", 1e9)
TERABIT_PER_SECOND = Bandwidth("Tbit/s", 1e12)
BYTE_PER_SECOND = Bandwidth("B/s", 8.0)
KILOBYTE_PER_SECOND = Bandwidth("KB/s", 8_000.0)
MEGABYTE_PER_SECOND = Bandwidth("MB/s", 8e6)
GIGABYTE_PER_SECOND = Bandwidth("GB/s", 8e9)
