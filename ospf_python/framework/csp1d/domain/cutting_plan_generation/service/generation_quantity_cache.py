"""CSP1D 生成数量缓存。

缓存切割方案中各产品的生成数量。
Caches generated quantities for products in cutting plans.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationQuantityCache:
    """生成数量缓存 / Generation quantity cache.

    缓存产品键到已生成数量的映射，
    用于跟踪各产品的累计生成量。
    Caches product key to generated quantity mapping,
    tracking cumulative generated quantities per product.

    Attributes:
        quantities: 产品键到数量的映射。
            Product key to quantity mapping.
    """

    quantities: tuple[tuple[str, int], ...] = ()
    """产品数量映射 / Product quantity mapping."""

    def get(self, product_key: str) -> int:
        """获取指定产品的数量。

        Get quantity for the specified product.

        Args:
            product_key: 产品键。
                Product key.

        Returns:
            产品数量，不存在返回 0。
            Product quantity, 0 if not found.
        """
        for key, qty in self.quantities:
            if key == product_key:
                return qty
        return 0

    def put(
        self,
        product_key: str,
        quantity: int,
    ) -> GenerationQuantityCache:
        """添加或更新产品数量。

        Add or update product quantity.

        Args:
            product_key: 产品键。
                Product key.
            quantity: 数量。
                Quantity.

        Returns:
            包含新数量的缓存实例。
            Cache instance with new quantity.
        """
        new_quantities = tuple(
            (k, q) for k, q in self.quantities if k != product_key
        ) + ((product_key, quantity),)
        return GenerationQuantityCache(quantities=new_quantities)

    def add(
        self,
        product_key: str,
        delta: int,
    ) -> GenerationQuantityCache:
        """累加产品数量。

        Accumulate product quantity.

        Args:
            product_key: 产品键。
                Product key.
            delta: 增量。
                Quantity delta.

        Returns:
            更新后的缓存实例。
            Updated cache instance.
        """
        current = self.get(product_key)
        return self.put(product_key, current + delta)

    def contains(self, product_key: str) -> bool:
        """检查是否包含指定产品。

        Check if cache contains the specified product.

        Args:
            product_key: 产品键。
                Product key.

        Returns:
            包含返回 True / True if contained.
        """
        return any(k == product_key for k, _ in self.quantities)

    @property
    def total_quantity(self) -> int:
        """获取所有产品的总数量。

        Get total quantity across all products.

        Returns:
            总数量。
            Total quantity.
        """
        return sum(q for _, q in self.quantities)

    @property
    def product_keys(self) -> tuple[str, ...]:
        """获取所有产品键。

        Get all product keys.

        Returns:
            产品键元组。
            Tuple of product keys.
        """
        return tuple(k for k, _ in self.quantities)

    @property
    def is_empty(self) -> bool:
        """判断缓存是否为空。

        Check if cache is empty.

        Returns:
            无产品数量时返回 True。
            True when no product quantities.
        """
        return len(self.quantities) == 0
