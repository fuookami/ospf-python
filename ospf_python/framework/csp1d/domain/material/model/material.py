"""CSP1D 材料模型 / CSP1D material model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    """原材料定义 / Raw material definition.

    描述可用于切割的原材料的物理属性和成本。
    Describes the physical properties and cost of a
    raw material available for cutting.

    Attributes:
        name: 材料名称 / Material name.
        width: 材料宽度 / Material width.
        length: 材料长度 / Material length.
        cost: 材料单价 / Material unit cost.
    """

    name: str
    width: float
    length: float
    cost: float
