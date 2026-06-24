"""CSP1D 产品模型 / CSP1D product model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    """产品定义 / Product definition.

    描述需要从原材料上切割产出的产品规格和需求量。
    Describes the specification and demand quantity of
    a product to be cut from raw materials.

    Attributes:
        name: 产品名称 / Product name.
        width: 产品宽度 / Product width.
        length: 产品长度 / Product length.
        demand: 需求量 / Demand quantity.
    """

    name: str
    width: float
    length: float
    demand: int
