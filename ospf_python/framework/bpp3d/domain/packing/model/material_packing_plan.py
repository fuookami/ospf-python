"""物料装箱计划 / Material packing plan.

表示物料的装箱计划。
Represents a packing plan for materials.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MaterialPackingPlan:
    """物料装箱计划 / Material packing plan.

    定义物料如何被装入容器。
    Defines how materials are packed into containers.

    Attributes:
        material_id: 物料标识 / The material identifier.
        container_id: 容器标识 / The container identifier.
        quantity: 装箱数量 / The packing quantity.
        position: 装箱位置 / The packing position.
    """

    material_id: str = ""
    container_id: str = ""
    quantity: int = 0
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
