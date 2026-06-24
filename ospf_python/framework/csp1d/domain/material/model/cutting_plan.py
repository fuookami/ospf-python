"""CSP1D 切割方案模型 / CSP1D cutting plan model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.csp1d.domain.material.model.product import (
        Product,
    )


@dataclass(frozen=True)
class CuttingPlan:
    """切割方案定义 / Cutting plan definition.

    描述从一种原材料上切割出若干产品的方案及其余料。
    Describes a plan for cutting multiple products
    from a single material and the resulting waste.

    Attributes:
        material: 所用原材料名称 / Name of the material used.
        products: 产品及其数量的元组 / Tuple of (product, quantity)
            pairs produced by this plan.
        waste: 余料宽度 / Remaining waste width.
    """

    material: str
    products: tuple[tuple[Product, int], ...]
    waste: float
