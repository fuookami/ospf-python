"""需求统计 / Demand statistics.

BPP3D 中物品需求的统计信息。
Demand statistics for items in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DemandStatistics:
    """需求统计 / Demand statistics.

    描述物品需求的统计摘要。
    Describes statistical summary of item demand.

    Attributes:
        item_key: 物品键 / Item key.
        total_demand: 总需求 / Total demand.
        fulfilled_demand: 已满足需求 / Fulfilled demand.
    """

    item_key: str
    """物品键 / Item key."""

    total_demand: int
    """总需求 / Total demand."""

    fulfilled_demand: int
    """已满足需求 / Fulfilled demand."""

    @staticmethod
    def create(
        *,
        item_key: str,
        total_demand: int,
        fulfilled_demand: int = 0,
    ) -> DemandStatistics:
        """创建需求统计 / Create demand statistics.

        Args:
            item_key: 物品键 / Item key.
            total_demand: 总需求 / Total demand.
            fulfilled_demand: 已满足需求，默认 0 /
                Fulfilled, default 0.

        Returns:
            需求统计实例 / DemandStatistics instance.
        """
        return DemandStatistics(
            item_key=item_key,
            total_demand=total_demand,
            fulfilled_demand=fulfilled_demand,
        )

    @property
    def remaining_demand(self) -> int:
        """剩余需求 / Remaining demand.

        Returns:
            总需求减已满足 / Total minus fulfilled.
        """
        return self.total_demand - self.fulfilled_demand

    @property
    def fulfillment_ratio(self) -> float:
        """满足率 / Fulfillment ratio.

        Returns:
            已满足除以总需求 / Fulfilled over total.
        """
        if self.total_demand == 0:
            return 0.0
        return self.fulfilled_demand / self.total_demand
