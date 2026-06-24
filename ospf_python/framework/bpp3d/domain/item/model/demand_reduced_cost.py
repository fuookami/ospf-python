"""需求缩减成本 / Demand reduced cost.

BPP3D 中物品需求的缩减成本。
Reduced cost for item demand in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DemandReducedCost:
    """需求缩减成本 / Demand reduced cost.

    描述物品需求的缩减成本值。
    Describes the reduced cost value for item demand.

    Attributes:
        item_key: 物品键 / Item key.
        reduced_cost: 缩减成本 / Reduced cost.
    """

    item_key: str
    """物品键 / Item key."""

    reduced_cost: float
    """缩减成本 / Reduced cost."""

    @staticmethod
    def create(
        *,
        item_key: str,
        reduced_cost: float,
    ) -> DemandReducedCost:
        """创建需求缩减成本 / Create demand reduced cost.

        Args:
            item_key: 物品键 / Item key.
            reduced_cost: 缩减成本 / Reduced cost.

        Returns:
            需求缩减成本实例 / DemandReducedCost instance.
        """
        return DemandReducedCost(
            item_key=item_key,
            reduced_cost=reduced_cost,
        )
