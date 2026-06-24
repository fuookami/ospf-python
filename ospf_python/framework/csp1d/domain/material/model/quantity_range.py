"""CSP1D 数量范围模型 / CSP1D quantity range model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuantityRange:
    """数量取值范围 / Quantity value range.

    描述切割方案中某个产品的生产数量上下界。
    Describes the upper and lower bounds of a
    product's production quantity in a cutting plan.

    Attributes:
        min_qty: 最小数量 / Minimum quantity.
        max_qty: 最大数量 / Maximum quantity.
    """

    min_qty: int
    max_qty: int
