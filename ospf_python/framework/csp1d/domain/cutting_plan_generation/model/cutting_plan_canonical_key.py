"""CSP1D 切割方案规范键。

用于唯一标识切割方案的组合模式。
Canonical key for uniquely identifying cutting plan patterns.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CuttingPlanCanonicalKey:
    """切割方案规范键 / Cutting plan canonical key.

    通过对产品-数量对排序生成规范表示，
    确保相同组合模式的切割方案具有相同键。
    Generates canonical representation by sorting
    product-quantity pairs, ensuring identical
    combination patterns share the same key.

    Attributes:
        pattern: 产品-数量对的有序元组，
            格式为 ((product_key, quantity), ...)。
            Sorted tuple of (product_key, quantity) pairs.
    """

    pattern: tuple[tuple[str, int], ...] = ()
    """产品-数量对的有序元组 / Sorted product-quantity pairs."""

    @staticmethod
    def create(
        *,
        items: dict[str, int],
    ) -> CuttingPlanCanonicalKey:
        """从产品-数量字典创建规范键。

        Create canonical key from product-quantity dict.

        Args:
            items: 产品键到数量的映射。
                Product key to quantity mapping.

        Returns:
            规范化的切割方案键。
            Canonicalized cutting plan key.
        """
        sorted_pairs = tuple(sorted(items.items(), key=lambda kv: kv[0]))
        return CuttingPlanCanonicalKey(pattern=sorted_pairs)

    @staticmethod
    def from_pairs(
        *,
        pairs: tuple[tuple[str, int], ...],
    ) -> CuttingPlanCanonicalKey:
        """从产品-数量对创建规范键。

        Create canonical key from product-quantity pairs.

        Args:
            pairs: 产品-数量对。
                Product-quantity pairs.

        Returns:
            规范化的切割方案键。
            Canonicalized cutting plan key.
        """
        sorted_pairs = tuple(sorted(pairs, key=lambda kv: kv[0]))
        return CuttingPlanCanonicalKey(pattern=sorted_pairs)

    @property
    def product_keys(self) -> tuple[str, ...]:
        """获取所有产品键。

        Get all product keys.

        Returns:
            产品键元组。
            Tuple of product keys.
        """
        return tuple(k for k, _ in self.pattern)

    @property
    def total_quantity(self) -> int:
        """获取总切割数量。

        Get total cut quantity.

        Returns:
            所有产品数量之和。
            Sum of all product quantities.
        """
        return sum(q for _, q in self.pattern)

    def contains_product(self, product_key: str) -> bool:
        """检查是否包含指定产品。

        Check if contains the specified product.

        Args:
            product_key: 产品键 / Product key.

        Returns:
            包含返回 True / True if contained.
        """
        return any(k == product_key for k, _ in self.pattern)

    def quantity_of(self, product_key: str) -> int:
        """获取指定产品的数量。

        Get quantity of the specified product.

        Args:
            product_key: 产品键 / Product key.

        Returns:
            产品数量，不存在返回 0。
            Product quantity, 0 if not found.
        """
        for k, q in self.pattern:
            if k == product_key:
                return q
        return 0
