"""舱室装载模型。

Compartment loading model for tracking per-compartment loading state.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompartmentLoading:
    """单个舱室的装载状态。

    Represents the loading state of a single compartment including
    its items, total weight, and volume usage.

    Attributes:
        compartment_id: 舱室标识 / Compartment identifier
        items: 装载物品ID列表 / List of loaded item IDs
        weight: 当前总重量（千克）/ Current total weight (kg)
        volume: 当前使用体积（立方米）/ Current used volume (m³)
    """

    compartment_id: str
    items: tuple[str, ...]
    weight: float
    volume: float

    def item_count(self) -> int:
        """计算物品数量。

        Returns:
            int: 物品数量 / Number of items
        """
        return len(self.items)

    def average_weight_per_item(self) -> float:
        """计算单件平均重量。

        Returns:
            float: 平均重量，无物品时返回0 / Average weight, 0 if no items
        """
        if not self.items:
            return 0.0
        return self.weight / len(self.items)

    def add_item(
        self,
        item_id: str,
        *,
        item_weight: float,
        item_volume: float,
    ) -> CompartmentLoading:
        """添加物品，返回新的装载状态（不可变操作）。

        Adds an item and returns a new loading state (immutable operation).

        Args:
            item_id: 物品标识 / Item identifier
            item_weight: 物品重量 / Item weight in kg
            item_volume: 物品体积 / Item volume in m³

        Returns:
            CompartmentLoading: 更新后的装载状态 / Updated loading state
        """
        return CompartmentLoading(
            compartment_id=self.compartment_id,
            items=(*self.items, item_id),
            weight=self.weight + item_weight,
            volume=self.volume + item_volume,
        )
