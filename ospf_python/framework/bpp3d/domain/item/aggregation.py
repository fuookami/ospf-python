"""物品聚合 / Item aggregation.

BPP3D 中物品的聚合操作。
Item aggregation operations in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Aggregation:
    """物品聚合 / Item aggregation.

    描述同类物品的聚合信息。
    Describes aggregation information for items of
    the same type.

    Attributes:
        item_key: 物品键 / Item key.
        count: 聚合数量 / Aggregation count.
    """

    item_key: str
    """物品键 / Item key."""

    count: int
    """聚合数量 / Aggregation count."""

    @staticmethod
    def create(
        *,
        item_key: str,
        count: int = 1,
    ) -> Aggregation:
        """创建聚合 / Create aggregation.

        Args:
            item_key: 物品键 / Item key.
            count: 聚合数量，默认 1 / Count, default 1.

        Returns:
            聚合实例 / Aggregation instance.
        """
        return Aggregation(
            item_key=item_key,
            count=count,
        )
