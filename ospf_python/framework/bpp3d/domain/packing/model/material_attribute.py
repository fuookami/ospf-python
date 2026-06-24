"""物料属性 / Material attribute.

表示物料的物理属性。
Represents physical attributes of a material.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MaterialAttribute:
    """物料属性 / Material attribute.

    描述物料的尺寸和重量等属性。
    Describes attributes such as dimensions and weight of
    a material.

    Attributes:
        width: 宽度 / The width.
        height: 高度 / The height.
        depth: 深度 / The depth.
        weight: 重量 / The weight.
        is_fragile: 是否易碎 / Whether fragile.
        is_cylindrical: 是否圆柱形 / Whether cylindrical.
    """

    width: float = 0.0
    height: float = 0.0
    depth: float = 0.0
    weight: float = 0.0
    is_fragile: bool = False
    is_cylindrical: bool = False
