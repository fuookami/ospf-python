"""时间单位。/ Time units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeUnit:
    """时间单位。/ Time unit.

    SI 基本单位为秒 (s)。/ SI base unit is second (s).
    """

    _symbol: str = "s"
    _factor: float = 1.0  # 转换到 SI 基本单位的系数 / factor to SI base

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（秒）。/ Convert value to SI (second)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（秒）转换值。/ Convert value from SI (second)."""
        return value / self._factor


# 预定义时间单位 / Predefined time units
SECOND = TimeUnit("s", 1.0)
MILLISECOND = TimeUnit("ms", 0.001)
MICROSECOND = TimeUnit("us", 1e-6)
NANOSECOND = TimeUnit("ns", 1e-9)
MINUTE = TimeUnit("min", 60.0)
HOUR = TimeUnit("h", 3_600.0)
DAY = TimeUnit("d", 86_400.0)
WEEK = TimeUnit("wk", 604_800.0)
YEAR = TimeUnit("yr", 31_557_600.0)  # 儒略年 / Julian year
