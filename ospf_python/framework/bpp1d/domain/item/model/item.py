"""物品定义 / Item definition.

BPP1D 中的一维物品定义。
One-dimensional item definition in BPP1D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    """物品 / Item.

    描述 BPP1D 中需要装入箱子的一维物品。
    Describes a one-dimensional item to be packed in BPP1D.

    Attributes:
        item_key: 物品键 / Item key.
        width: 物品宽度（一维尺寸）/ Item width (1D size).
        height: 物品高度 / Item height.
        weight: 物品重量 / Item weight.
    """

    item_key: str
    """物品键 / Item key."""

    width: float
    """物品宽度（一维尺寸）/ Item width (1D size)."""

    height: float
    """物品高度 / Item height."""

    weight: float = 0.0
    """物品重量，默认 0 / Item weight, default 0."""

    @staticmethod
    def create(
        *,
        item_key: str,
        width: float,
        height: float,
        weight: float = 0.0,
    ) -> Item:
        """创建物品 / Create item.

        Args:
            item_key: 物品键 / Item key.
            width: 物品宽度 / Item width.
            height: 物品高度 / Item height.
            weight: 物品重量，默认 0 / Weight, default 0.

        Returns:
            物品实例 / Item instance.
        """
        return Item(
            item_key=item_key,
            width=width,
            height=height,
            weight=weight,
        )

    @property
    def area(self) -> float:
        """物品面积 / Item area.

        Returns:
            宽 x 高 / Width x Height.
        """
        return self.width * self.height
