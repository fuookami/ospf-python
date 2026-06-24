"""物料装箱数量 / Material packing numbers.

记录物料的装箱数量信息。
Records packing quantity information for materials.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MaterialPackingNumbers:
    """物料装箱数量 / Material packing numbers.

    记录物料在装箱方案中的分配数量。
    Records allocation quantities of a material in packing
    solutions.

    Attributes:
        material_id: 物料标识 / The material identifier.
        packed_quantity: 已装箱数量 / The packed quantity.
        remaining_quantity: 剩余数量 / The remaining quantity.
    """

    material_id: str = ""
    packed_quantity: int = 0
    remaining_quantity: int = 0
