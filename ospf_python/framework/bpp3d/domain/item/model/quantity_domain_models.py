"""数量域模型 / Quantity domain models.

BPP3D 中数量相关的域模型集合。
Collection of quantity-related domain models in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuantityDomainModels:
    """数量域模型 / Quantity domain models.

    聚合数量相关的域模型。
    Aggregates quantity-related domain models.

    Attributes:
        model_id: 模型标识 / Model identifier.
        item_count: 物品种类数 / Item type count.
        total_quantity: 总需求数量 / Total demand quantity.
    """

    model_id: str
    """模型标识 / Model identifier."""

    item_count: int
    """物品种类数 / Item type count."""

    total_quantity: int
    """总需求数量 / Total demand quantity."""

    @staticmethod
    def create(
        *,
        model_id: str,
        item_count: int = 0,
        total_quantity: int = 0,
    ) -> QuantityDomainModels:
        """创建数量域模型 / Create quantity domain models.

        Args:
            model_id: 模型标识 / Model identifier.
            item_count: 物品种类数，默认 0 /
                Item count, default 0.
            total_quantity: 总数量，默认 0 /
                Total quantity, default 0.

        Returns:
            数量域模型实例 / QuantityDomainModels instance.
        """
        return QuantityDomainModels(
            model_id=model_id,
            item_count=item_count,
            total_quantity=total_quantity,
        )
