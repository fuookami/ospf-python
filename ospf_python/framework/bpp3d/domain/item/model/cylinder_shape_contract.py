"""圆柱体形状契约 / Cylinder shape contract.

BPP3D 中圆柱体形状的契约定义。
Cylinder shape contract definition in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp3d.infrastructure.cylinder import (
        Cylinder,
    )


@dataclass(frozen=True)
class CylinderShapeContract:
    """圆柱体形状契约。

    描述圆柱体物品的形状约束和允许的方向。
    Describes shape constraints and allowed orientations
    for a cylinder item.

    Attributes:
        cylinder: 圆柱体形状 / Cylinder shape.
        allow_horizontal: 允许水平放置 /
            Allow horizontal placement.
        allow_vertical: 允许垂直放置 /
            Allow vertical placement.
    """

    cylinder: Cylinder
    """圆柱体形状 / Cylinder shape."""

    allow_horizontal: bool = True
    """允许水平放置 / Allow horizontal placement."""

    allow_vertical: bool = True
    """允许垂直放置 / Allow vertical placement."""

    @staticmethod
    def create(
        *,
        cylinder: Cylinder,
        allow_horizontal: bool = True,
        allow_vertical: bool = True,
    ) -> CylinderShapeContract:
        """创建形状契约 / Create shape contract.

        Args:
            cylinder: 圆柱体形状 / Cylinder shape.
            allow_horizontal: 允许水平，默认 True /
                Allow horizontal, default True.
            allow_vertical: 允许垂直，默认 True /
                Allow vertical, default True.

        Returns:
            形状契约实例 / Shape contract instance.
        """
        return CylinderShapeContract(
            cylinder=cylinder,
            allow_horizontal=allow_horizontal,
            allow_vertical=allow_vertical,
        )
