"""投影平面几何映射 / Projective plane geometry mapping.

将三维放置映射到二维投影平面。
Maps 3D placement to 2D projection plane.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp3d.infrastructure.projection import (
        Projection,
    )


@dataclass(frozen=True)
class ProjectivePlaneGeometryMapping:
    """投影平面几何映射。

    管理三维物体到二维投影平面的几何变换。
    Manages geometric transformation from 3D objects
    to 2D projection planes.

    Attributes:
        projection: 二维投影 / 2D projection.
        offset_x: X 方向偏移 / X direction offset.
        offset_y: Y 方向偏移 / Y direction offset.
    """

    projection: Projection
    """二维投影 / 2D projection."""

    offset_x: float
    """X 方向偏移 / X direction offset."""

    offset_y: float
    """Y 方向偏移 / Y direction offset."""

    @staticmethod
    def create(
        *,
        projection: Projection,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ) -> ProjectivePlaneGeometryMapping:
        """创建映射 / Create mapping.

        Args:
            projection: 二维投影 / 2D projection.
            offset_x: X 偏移，默认 0 / X offset, default 0.
            offset_y: Y 偏移，默认 0 / Y offset, default 0.

        Returns:
            平面几何映射实例 / Plane geometry mapping.
        """
        return ProjectivePlaneGeometryMapping(
            projection=projection,
            offset_x=offset_x,
            offset_y=offset_y,
        )

    @property
    def center_x(self) -> float:
        """投影中心 X / Projection center X.

        Returns:
            偏移加投影宽度一半 / Offset plus half width.
        """
        return self.offset_x + self.projection.width / 2.0

    @property
    def center_y(self) -> float:
        """投影中心 Y / Projection center Y.

        Returns:
            偏移加投影高度一半 / Offset plus half height.
        """
        return self.offset_y + self.projection.height / 2.0
