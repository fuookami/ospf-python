"""投影定义 / Projection definition.

BPP3D 中物品在平面上的投影。
Item projection on a plane in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Projection:
    """投影 / Projection.

    描述物品在某一平面上的二维投影尺寸。
    Describes the 2D projection dimensions of an item
    on a plane.

    Attributes:
        width: 投影宽度 / Projection width.
        height: 投影高度 / Projection height.
    """

    width: float
    """投影宽度 / Projection width."""

    height: float
    """投影高度 / Projection height."""

    @staticmethod
    def create(
        *,
        width: float,
        height: float,
    ) -> Projection:
        """创建投影 / Create projection.

        Args:
            width: 投影宽度 / Projection width.
            height: 投影高度 / Projection height.

        Returns:
            投影实例 / Projection instance.
        """
        return Projection(
            width=width,
            height=height,
        )

    @property
    def area(self) -> float:
        """投影面积 / Projection area.

        Returns:
            宽 x 高 / Width x Height.
        """
        return self.width * self.height
