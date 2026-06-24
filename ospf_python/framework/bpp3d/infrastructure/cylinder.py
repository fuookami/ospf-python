"""圆柱体形状 / Cylinder shape.

BPP3D 中圆柱体物品的形状定义。
Cylinder item shape definition in BPP3D.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Cylinder:
    """圆柱体形状 / Cylinder shape.

    描述圆柱体物品的半径和高度。
    Describes the radius and height of a cylinder item.

    Attributes:
        radius: 圆柱半径 / Cylinder radius.
        height: 圆柱高度 / Cylinder height.
    """

    radius: float
    """圆柱半径 / Cylinder radius."""

    height: float
    """圆柱高度 / Cylinder height."""

    @staticmethod
    def create(
        *,
        radius: float,
        height: float,
    ) -> Cylinder:
        """创建圆柱体形状 / Create cylinder shape.

        Args:
            radius: 圆柱半径 / Cylinder radius.
            height: 圆柱高度 / Cylinder height.

        Returns:
            圆柱体形状实例 / Cylinder shape instance.
        """
        return Cylinder(
            radius=radius,
            height=height,
        )

    @property
    def diameter(self) -> float:
        """直径 / Diameter.

        Returns:
            2 倍半径 / 2 times radius.
        """
        return 2.0 * self.radius

    @property
    def volume(self) -> float:
        """体积 / Volume.

        Returns:
            pi * r^2 * h / pi * r^2 * h.
        """
        return math.pi * self.radius**2 * self.height
