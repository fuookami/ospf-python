"""物品合并器 / Item merger.

BPP3D 中同类物品的合并操作。
Merge operation for identical items in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.framework.bpp3d.domain.item.model.item import Item


@dataclass(frozen=True)
class ItemMerger:
    """物品合并器 / Item merger.

    合并相同尺寸的物品以减少问题规模。
    Merges items with same dimensions to reduce
    problem size.

    Attributes:
        merge_threshold: 合并阈值 / Merge threshold.
    """

    merge_threshold: float = 1e-6
    """合并阈值 / Merge threshold."""

    @staticmethod
    def create(
        *,
        merge_threshold: float = 1e-6,
    ) -> ItemMerger:
        """创建合并器 / Create merger.

        Args:
            merge_threshold: 阈值，默认 1e-6 /
                Threshold, default 1e-6.

        Returns:
            物品合并器实例 / ItemMerger instance.
        """
        return ItemMerger(merge_threshold=merge_threshold)

    def can_merge(self, item_a: Item, item_b: Item) -> bool:
        """判断两物品是否可合并 / Check if items can merge.

        Args:
            item_a: 物品 A / Item A.
            item_b: 物品 B / Item B.

        Returns:
            是否可合并 / Whether can merge.
        """
        return (
            abs(item_a.width - item_b.width) < self.merge_threshold
            and abs(item_a.height - item_b.height) < self.merge_threshold
            and abs(item_a.depth - item_b.depth) < self.merge_threshold
        )

    def merge(
        self,
        item_a: Item,
        item_b: Item,
    ) -> Item:
        """合并两个物品 / Merge two items.

        Args:
            item_a: 物品 A / Item A.
            item_b: 物品 B / Item B.

        Returns:
            合并后的物品 / Merged item.
        """
        return Item.create(
            item_key=item_a.item_key,
            width=item_a.width,
            height=item_a.height,
            depth=item_a.depth,
            quantity=item_a.quantity + item_b.quantity,
        )
