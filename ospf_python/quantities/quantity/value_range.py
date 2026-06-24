"""物理量值范围。/ Physical quantity value range."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.quantities.quantity.quantity import Quantity


@dataclass(frozen=True)
class QuantityValueRange:
    """物理量值范围，由最小值和最大值界定。

    Physical quantity value range bounded by
    minimum and maximum quantities.

    Attributes:
        min_qty: 最小值。/ Minimum quantity.
        max_qty: 最大值。/ Maximum quantity.
    """

    min_qty: Quantity[float]
    max_qty: Quantity[float]

    def contains(self, qty: Quantity[float]) -> bool:
        """检查物理量是否在范围内。

        Check if quantity is within range.

        通过 SI 中间值进行比较。
        Compares via SI intermediate values.

        Args:
            qty: 待检查的物理量。
                Quantity to check.

        Returns:
            是否在范围内。/ Whether in range.
        """
        min_si = self.min_qty.unit.to_si(float(self.min_qty.value))
        max_si = self.max_qty.unit.to_si(float(self.max_qty.value))
        val_si = qty.unit.to_si(float(qty.value))
        return min_si <= val_si <= max_si
