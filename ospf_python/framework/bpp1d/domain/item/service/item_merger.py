"""物品合并器 / Item merger.

BPP1D 中物品的合并逻辑。
Item merging logic in BPP1D.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.framework.bpp1d.domain.item.model.item import Item


@dataclass(frozen=True)
class ItemMerger:
    """物品合并器 / Item merger.

    将多个相同物品合并为一个带数量的物品。
    Merges multiple identical items into one with quantity.

    Attributes:
        tolerance: 尺寸容差 / Size tolerance.
    """

    tolerance: float = 1e-9
    """尺寸容差 / Size tolerance."""

    @staticmethod
    def create(
        *,
        tolerance: float = 1e-9,
    ) -> ItemMerger:
        """创建合并器 / Create merger.

        Args:
            tolerance: 容差，默认 1e-9 / Tolerance, default 1e-9.

        Returns:
            合并器实例 / ItemMerger instance.
        """
        return ItemMerger(tolerance=tolerance)

    def merge_duplicates(
        self,
        items: tuple[Item, ...],
    ) -> tuple[Item, ...]:
        """合并重复物品 / Merge duplicate items.

        将宽度和高度相同的物品合并。
        Merges items with same width and height.

        Args:
            items: 待合并物品 / Items to merge.

        Returns:
            合并后的物品元组 / Merged items tuple.
        """
        groups: dict[tuple[float, float], list[Item]] = {}
        for item in items:
            key = (
                round(item.width / self.tolerance) * self.tolerance,
                round(item.height / self.tolerance) * self.tolerance,
            )
            if key not in groups:
                groups[key] = []
            groups[key].append(item)

        merged: list[Item] = []
        for group_items in groups.values():
            first = group_items[0]
            total_weight = sum(i.weight for i in group_items)
            merged.append(
                Item.create(
                    item_key=first.item_key,
                    width=first.width,
                    height=first.height,
                    weight=total_weight,
                )
            )
        return tuple(merged)

    def sort_by_width_desc(
        self,
        items: tuple[Item, ...],
    ) -> tuple[Item, ...]:
        """按宽度降序排序 / Sort by width descending.

        Args:
            items: 待排序物品 / Items to sort.

        Returns:
            排序后的物品元组 / Sorted items tuple.
        """
        return tuple(sorted(items, key=lambda i: i.width, reverse=True))

    def filter_fit(
        self,
        items: tuple[Item, ...],
        *,
        capacity: float,
    ) -> tuple[Item, ...]:
        """过滤可装入物品 / Filter items that fit.

        Args:
            items: 待过滤物品 / Items to filter.
            capacity: 箱子容量 / Bin capacity.

        Returns:
            宽度不超过容量的物品。
            Items whose width does not exceed capacity.
        """
        return tuple(item for item in items if item.width <= capacity + self.tolerance)
