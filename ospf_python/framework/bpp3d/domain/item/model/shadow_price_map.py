"""物品影子价格映射 / Item shadow price map.

BPP3D 物品域的影子价格映射。
Shadow price map for BPP3D item domain.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ItemShadowPriceMap:
    """物品影子价格映射。

    存储物品需求约束的影子价格。
    Stores shadow prices for item demand constraints.

    Attributes:
        prices: 物品键到影子价格的映射 /
            Item key to shadow price mapping.
    """

    prices: tuple[tuple[str, float], ...]
    """物品键到影子价格的映射 /
    Item key to shadow price mapping."""

    @staticmethod
    def create(
        *,
        prices: tuple[tuple[str, float], ...],
    ) -> ItemShadowPriceMap:
        """创建映射 / Create mapping.

        Args:
            prices: 价格元组 / Price tuples.

        Returns:
            物品影子价格映射 / ItemShadowPriceMap instance.
        """
        return ItemShadowPriceMap(prices=prices)

    def get_price(self, item_key: str) -> float:
        """获取影子价格 / Get shadow price.

        Args:
            item_key: 物品键 / Item key.

        Returns:
            影子价格，未找到返回 0 / Price, 0 if not found.
        """
        for key, price in self.prices:
            if key == item_key:
                return price
        return 0.0

    @property
    def item_count(self) -> int:
        """物品数量 / Item count.

        Returns:
            价格元组长度 / Length of price tuples.
        """
        return len(self.prices)
