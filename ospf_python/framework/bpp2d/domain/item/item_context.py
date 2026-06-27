"""物品上下文 / Item context.

管理 BPP2D 物品的注册与查询。
Manages registration and lookup of BPP2D items.
"""

from __future__ import annotations

from ospf_python.framework.bpp2d.domain.item.error.bpp2d_errors import (
    Bpp2dErrors,
)
from ospf_python.framework.bpp2d.domain.item.model.circle import (
    Circle,
)
from ospf_python.framework.bpp2d.domain.item.model.rectangle import (
    Rectangle,
)
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok, Result

# 物品类型联合 / Item type union
Item = Rectangle | Circle


class ItemContext:
    """物品上下文 / Item context.

    维护物品注册表，提供物品的注册、查询和管理功能。
    在二维装箱中充当物品的中央仓库。
    Maintains the item registry, providing registration,
    query, and management functions. Acts as the central
    repository for items in 2D bin packing.

    Attributes:
        _items: 内部物品字典 / Internal item dictionary.
    """

    def __init__(self) -> None:
        """初始化空物品上下文 / Initialize empty item context."""
        self._items: dict[str, Item] = {}

    def register(
        self,
        item: Item,
    ) -> Result[None, str, Err[str]]:
        """注册物品 / Register an item.

        如果物品键已存在，返回失败结果。
        Returns a failure result if the item key exists.

        Args:
            item: 要注册的物品 / Item to register.

        Returns:
            注册结果 / Registration result.
        """
        if item.item_key in self._items:
            return Failed(
                Err(
                    _code=Bpp2dErrors.DUPLICATE_ITEM.value,
                    _message=(
                        f"物品键已存在: {item.item_key} / "
                        f"Item key already exists: "
                        f"{item.item_key}"
                    ),
                )
            )
        self._items[item.item_key] = item
        return Ok(None)

    def unregister(
        self,
        item_key: str,
    ) -> Result[None, str, Err[str]]:
        """注销物品 / Unregister an item.

        Args:
            item_key: 物品键 / Item key.

        Returns:
            注销结果 / Unregistration result.
        """
        if item_key not in self._items:
            return Failed(
                Err(
                    _code=Bpp2dErrors.ITEM_NOT_FOUND.value,
                    _message=(f"物品未找到: {item_key} / Item not found: {item_key}"),
                )
            )
        del self._items[item_key]
        return Ok(None)

    def get(self, key: str) -> Item | None:
        """获取物品 / Get an item.

        Args:
            key: 物品键 / Item key.

        Returns:
            物品实例或 None / Item instance or None.
        """
        return self._items.get(key)

    def get_or_error(
        self,
        key: str,
    ) -> Result[Item, str, Err[str]]:
        """获取物品或返回错误 / Get item or return error.

        Args:
            key: 物品键 / Item key.

        Returns:
            包含物品的成功结果或失败结果。
            Success result with item or failure result.
        """
        item = self._items.get(key)
        if item is None:
            return Failed(
                Err(
                    _code=Bpp2dErrors.ITEM_NOT_FOUND.value,
                    _message=(f"物品未找到: {key} / Item not found: {key}"),
                )
            )
        return Ok(item)

    def items(self) -> tuple[Item, ...]:
        """获取所有已注册物品 / Get all registered items.

        Returns:
            物品元组 / Item tuple.
        """
        return tuple(self._items.values())

    def item_keys(self) -> tuple[str, ...]:
        """获取所有物品键 / Get all item keys.

        Returns:
            物品键元组 / Item key tuple.
        """
        return tuple(self._items.keys())

    def rectangles(self) -> tuple[Rectangle, ...]:
        """获取所有矩形物品 / Get all rectangle items.

        Returns:
            矩形物品元组 / Rectangle item tuple.
        """
        from ospf_python.framework.bpp2d.domain.item.model.rectangle import (
            Rectangle,
        )

        return tuple(i for i in self._items.values() if isinstance(i, Rectangle))

    def circles(self) -> tuple[Circle, ...]:
        """获取所有圆形物品 / Get all circle items.

        Returns:
            圆形物品元组 / Circle item tuple.
        """
        from ospf_python.framework.bpp2d.domain.item.model.circle import (
            Circle,
        )

        return tuple(i for i in self._items.values() if isinstance(i, Circle))

    def contains(self, key: str) -> bool:
        """检查物品是否存在 / Check if item exists.

        Args:
            key: 物品键 / Item key.

        Returns:
            是否存在 / Whether exists.
        """
        return key in self._items

    @property
    def size(self) -> int:
        """获取物品数量 / Get item count.

        Returns:
            已注册物品数量 / Number of registered items.
        """
        return len(self._items)

    @property
    def is_empty(self) -> bool:
        """是否为空 / Whether empty.

        Returns:
            无注册物品时返回 True。
            True when no items registered.
        """
        return len(self._items) == 0

    @property
    def total_weight(self) -> float:
        """获取所有物品总重量 / Get total weight of all items.

        Returns:
            所有物品重量之和 / Sum of all item weights.
        """
        return sum(i.weight for i in self._items.values())

    def clear(self) -> None:
        """清空所有物品 / Clear all items."""
        self._items.clear()
