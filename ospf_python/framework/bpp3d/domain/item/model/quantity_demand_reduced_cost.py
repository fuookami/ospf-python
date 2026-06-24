"""数量需求缩减成本 / Quantity demand reduced cost.

BPP3D 中带数量的需求缩减成本。
Quantity-aware demand reduced cost in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuantityDemandReducedCost:
    """数量需求缩减成本。

    描述带数量信息的需求缩减成本。
    Describes demand reduced cost with quantity info.

    Attributes:
        item_key: 物品键 / Item key.
        quantity: 需求数量 / Demand quantity.
        reduced_cost: 缩减成本 / Reduced cost.
    """

    item_key: str
    """物品键 / Item key."""

    quantity: int
    """需求数量 / Demand quantity."""

    reduced_cost: float
    """缩减成本 / Reduced cost."""

    @staticmethod
    def create(
        *,
        item_key: str,
        quantity: int,
        reduced_cost: float,
    ) -> QuantityDemandReducedCost:
        """创建数量需求缩减成本 / Create quantity demand reduced cost.

        Args:
            item_key: 物品键 / Item key.
            quantity: 需求数量 / Demand quantity.
            reduced_cost: 缩减成本 / Reduced cost.

        Returns:
            实例 / Instance.
        """
        return QuantityDemandReducedCost(
            item_key=item_key,
            quantity=quantity,
            reduced_cost=reduced_cost,
        )

    @property
    def total_reduced_cost(self) -> float:
        """总缩减成本 / Total reduced cost.

        Returns:
            数量乘缩减成本 / Quantity times reduced cost.
        """
        return self.quantity * self.reduced_cost
