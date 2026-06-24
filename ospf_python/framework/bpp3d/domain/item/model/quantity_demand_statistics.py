"""数量需求统计 / Quantity demand statistics.

BPP3D 中带数量的需求统计。
Quantity-aware demand statistics in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuantityDemandStatistics:
    """数量需求统计。

    描述带数量信息的需求统计。
    Describes demand statistics with quantity info.

    Attributes:
        item_key: 物品键 / Item key.
        total_quantity: 总数量 / Total quantity.
        packed_quantity: 已装箱数量 / Packed quantity.
    """

    item_key: str
    """物品键 / Item key."""

    total_quantity: int
    """总数量 / Total quantity."""

    packed_quantity: int = 0
    """已装箱数量 / Packed quantity."""

    @staticmethod
    def create(
        *,
        item_key: str,
        total_quantity: int,
        packed_quantity: int = 0,
    ) -> QuantityDemandStatistics:
        """创建统计 / Create statistics.

        Args:
            item_key: 物品键 / Item key.
            total_quantity: 总数量 / Total quantity.
            packed_quantity: 已装箱，默认 0 /
                Packed, default 0.

        Returns:
            统计实例 / Statistics instance.
        """
        return QuantityDemandStatistics(
            item_key=item_key,
            total_quantity=total_quantity,
            packed_quantity=packed_quantity,
        )

    @property
    def remaining_quantity(self) -> int:
        """剩余数量 / Remaining quantity.

        Returns:
            总数量减已装箱 / Total minus packed.
        """
        return self.total_quantity - self.packed_quantity

    @property
    def packing_ratio(self) -> float:
        """装箱率 / Packing ratio.

        Returns:
            已装箱除以总数量 / Packed over total.
        """
        if self.total_quantity == 0:
            return 0.0
        return self.packed_quantity / self.total_quantity
