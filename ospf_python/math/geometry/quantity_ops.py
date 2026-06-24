"""几何量与物理量桥接。

Bridge between geometry and physical quantities.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuantityOps:
    """几何量操作，提供标量到几何量的转换。

    Geometric quantity operations providing
    scalar-to-quantity conversion.

    Attributes:
        value: 数值。/ Numeric value.
        unit: 单位标签。/ Unit label.
    """

    value: float
    unit: str

    @staticmethod
    def length(value: float) -> QuantityOps:
        """创建长度量。/ Create length quantity."""
        return QuantityOps(value=value, unit="m")

    @staticmethod
    def area(value: float) -> QuantityOps:
        """创建面积量。/ Create area quantity."""
        return QuantityOps(value=value, unit="m^2")

    @staticmethod
    def volume(value: float) -> QuantityOps:
        """创建体积量。/ Create volume quantity."""
        return QuantityOps(value=value, unit="m^3")

    def __repr__(self) -> str:
        """字符串表示。/ String representation."""
        return f"{self.value} {self.unit}"
