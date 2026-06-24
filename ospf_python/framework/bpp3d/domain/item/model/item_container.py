"""物品容器 / Item container.

BPP3D 中物品与容器的关联。
Association of item with container in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp3d.domain.item.model.item import Item


@dataclass(frozen=True)
class ItemContainer:
    """物品容器 / Item container.

    将物品与特定容器关联。
    Associates an item with a specific container.

    Attributes:
        item: 物品 / Item.
        container_key: 容器键 / Container key.
    """

    item: Item
    """物品 / Item."""

    container_key: str
    """容器键 / Container key."""

    @staticmethod
    def create(
        *,
        item: Item,
        container_key: str,
    ) -> ItemContainer:
        """创建物品容器 / Create item container.

        Args:
            item: 物品 / Item.
            container_key: 容器键 / Container key.

        Returns:
            物品容器实例 / ItemContainer instance.
        """
        return ItemContainer(
            item=item,
            container_key=container_key,
        )
