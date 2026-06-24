"""物品定义 / Item definition.

BPP3D 中的物品定义。
Item definition in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    """物品 / Item.

    描述 BPP3D 中需要装箱的物品。
    Describes an item to be packed in BPP3D.

    Attributes:
        item_key: 物品键 / Item key.
        width: 物品宽度 / Item width.
        height: 物品高度 / Item height.
        depth: 物品深度 / Item depth.
        quantity: 需求数量 / Demand quantity.
    """

    item_key: str
    """物品键 / Item key."""

    width: float
    """物品宽度 / Item width."""

    height: float
    """物品高度 / Item height."""

    depth: float
    """物品深度 / Item depth."""

    quantity: int
    """需求数量 / Demand quantity."""

    @staticmethod
    def create(
        *,
        item_key: str,
        width: float,
        height: float,
        depth: float,
        quantity: int = 1,
    ) -> Item:
        """创建物品 / Create item.

        Args:
            item_key: 物品键 / Item key.
            width: 物品宽度 / Item width.
            height: 物品高度 / Item height.
            depth: 物品深度 / Item depth.
            quantity: 需求数量，默认 1 / Quantity, default 1.

        Returns:
            物品实例 / Item instance.
        """
        return Item(
            item_key=item_key,
            width=width,
            height=height,
            depth=depth,
            quantity=quantity,
        )

    @property
    def volume(self) -> float:
        """物品体积 / Item volume.

        Returns:
            宽 x 高 x 深 / Width x Height x Depth.
        """
        return self.width * self.height * self.depth

    @property
    def total_volume(self) -> float:
        """总体积 / Total volume.

        Returns:
            体积乘数量 / Volume times quantity.
        """
        return self.volume * self.quantity
