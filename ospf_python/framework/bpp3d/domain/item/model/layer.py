"""层定义 / Layer definition.

BPP3D 中的层定义。
Layer definition in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Layer:
    """层 / Layer.

    描述 BPP3D 中的一层物品排列。
    Describes a layer of item arrangement in BPP3D.

    Attributes:
        layer_id: 层标识 / Layer identifier.
        height: 层高度 / Layer height.
        item_keys: 物品键列表 / Item key list.
    """

    layer_id: str
    """层标识 / Layer identifier."""

    height: float
    """层高度 / Layer height."""

    item_keys: tuple[str, ...]
    """物品键列表 / Item key list."""

    @staticmethod
    def create(
        *,
        layer_id: str,
        height: float,
        item_keys: tuple[str, ...] = (),
    ) -> Layer:
        """创建层 / Create layer.

        Args:
            layer_id: 层标识 / Layer identifier.
            height: 层高度 / Layer height.
            item_keys: 物品键列表，默认空 /
                Item keys, default empty.

        Returns:
            层实例 / Layer instance.
        """
        return Layer(
            layer_id=layer_id,
            height=height,
            item_keys=item_keys,
        )

    @property
    def item_count(self) -> int:
        """物品数量 / Item count.

        Returns:
            物品键列表长度 / Length of item key list.
        """
        return len(self.item_keys)
