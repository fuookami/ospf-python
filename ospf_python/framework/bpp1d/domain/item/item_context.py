"""物品上下文 / Item context.

管理 BPP1D 物品的注册与查询。
Manages registration and lookup of BPP1D items.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp1d.domain.item.model.item import Item


@dataclass(frozen=True)
class ItemContext:
    """物品上下文 / Item context.

    持有已注册物品的字典，支持注册和查询操作。
    Holds a dictionary of registered items, supporting
    registration and lookup operations.

    Attributes:
        items: 已注册物品映射（键 -> 物品）/
            Registered items mapping (key -> item).
    """

    items: dict[str, Item] = field(
        default_factory=dict,
    )
    """已注册物品映射 / Registered items mapping."""

    @staticmethod
    def create(
        *,
        items: dict[str, Item] | None = None,
    ) -> ItemContext:
        """创建物品上下文 / Create item context.

        Args:
            items: 初始物品映射，默认空 /
                Initial items mapping, default empty.

        Returns:
            物品上下文实例 / ItemContext instance.
        """
        return ItemContext(
            items=dict(items) if items else {},
        )

    def register(self, item: Item) -> ItemContext:
        """注册物品 / Register item.

        将物品添加到上下文中。返回新的上下文实例。
        Adds an item to the context. Returns a new context.

        Args:
            item: 要注册的物品 / Item to register.

        Returns:
            包含新物品的上下文 / Context with the new item.
        """
        new_items = dict(self.items)
        new_items[item.item_key] = item
        return ItemContext(items=new_items)

    def register_many(
        self,
        items: tuple[Item, ...],
    ) -> ItemContext:
        """批量注册物品 / Register multiple items.

        Args:
            items: 要注册的物品元组 / Items tuple to register.

        Returns:
            包含所有新物品的上下文 /
            Context with all new items.
        """
        result = self
        for item in items:
            result = result.register(item)
        return result

    def get(self, item_key: str) -> Item | None:
        """查询物品 / Lookup item.

        Args:
            item_key: 物品键 / Item key.

        Returns:
            物品实例或 None / Item instance or None.
        """
        return self.items.get(item_key)

    def get_all(self) -> tuple[Item, ...]:
        """获取所有物品 / Get all items.

        Returns:
            所有已注册物品的元组。
            Tuple of all registered items.
        """
        return tuple(self.items.values())

    @property
    def count(self) -> int:
        """物品数量 / Item count.

        Returns:
            已注册物品的数量。
            Number of registered items.
        """
        return len(self.items)
