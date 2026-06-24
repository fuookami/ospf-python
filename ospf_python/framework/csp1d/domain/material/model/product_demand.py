"""CSP1D 产品需求模型 / CSP1D product demand model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductDemand:
    """产品需求定义 / Product demand definition.

    描述某个产品的具体需求量。
    Describes the specific demand quantity for a product.

    Attributes:
        product: 产品名称 / Product name.
        quantity: 需求量 / Demand quantity.
    """

    product: str
    quantity: int
