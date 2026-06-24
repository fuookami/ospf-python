"""长方体形状 / Cuboid shape.

BPP3D 中长方体物品的形状定义。
Cuboid item shape definition in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Cuboid:
    """长方体形状 / Cuboid shape.

    描述长方体物品的三维尺寸。
    Describes the three-dimensional dimensions of a
    cuboid item.

    Attributes:
        width: 宽度 / Width.
        height: 高度 / Height.
        depth: 深度 / Depth.
    """

    width: float
    """宽度 / Width."""

    height: float
    """高度 / Height."""

    depth: float
    """深度 / Depth."""

    @staticmethod
    def create(
        *,
        width: float,
        height: float,
        depth: float,
    ) -> Cuboid:
        """创建长方体形状 / Create cuboid shape.

        Args:
            width: 宽度 / Width.
            height: 高度 / Height.
            depth: 深度 / Depth.

        Returns:
            长方体形状实例 / Cuboid shape instance.
        """
        return Cuboid(
            width=width,
            height=height,
            depth=depth,
        )

    @property
    def volume(self) -> float:
        """体积 / Volume.

        Returns:
            宽 x 高 x 深 / Width x Height x Depth.
        """
        return self.width * self.height * self.depth
