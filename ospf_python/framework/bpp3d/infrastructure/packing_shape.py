"""装箱形状枚举 / Packing shape enumeration.

定义 BPP3D 中物品的装箱形状类型。
Defines packing shape types for items in BPP3D.
"""

from __future__ import annotations

import enum


class PackingShape(enum.Enum):
    """装箱形状枚举 / Packing shape enumeration.

    描述物品是长方体还是圆柱体。
    Describes whether an item is a cuboid or cylinder.

    Attributes:
        CUBOID: 长方体 / Cuboid.
        CYLINDER: 圆柱体 / Cylinder.
    """

    CUBOID = "cuboid"
    """长方体 / Cuboid."""

    CYLINDER = "cylinder"
    """圆柱体 / Cylinder."""
