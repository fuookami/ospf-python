"""电荷单位。/ Electric charge units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ElectricCharge:
    """电荷单位。/ Electric charge unit.

    SI 导出单位为库仑 (C)。/ SI derived unit is coulomb (C).
    """

    _symbol: str = "C"
    _factor: float = 1.0  # 转换到 SI 单位的系数 / factor to SI

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        return self._symbol

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位（库仑）。/ Convert to SI (coulomb)."""
        return value * self._factor

    def from_si(self, value: float) -> float:
        """从 SI 单位（库仑）转换值。/ Convert from SI (coulomb)."""
        return value / self._factor


# 预定义电荷单位 / Predefined electric charge units
COULOMB = ElectricCharge("C", 1.0)
MILLICOULOMB = ElectricCharge("mC", 0.001)
MICROCOULOMB = ElectricCharge("uC", 1e-6)
NANOCOULOMB = ElectricCharge("nC", 1e-9)
AMPERE_HOUR = ElectricCharge("Ah", 3_600.0)
MILLIAMPERE_HOUR = ElectricCharge("mAh", 3.6)
ELEMENTARY_CHARGE = ElectricCharge("e", 1.602176634e-19)
