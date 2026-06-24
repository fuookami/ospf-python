"""放置平面映射 / Placement plane mapping.

BPP3D 中放置到平面的映射。
Mapping from placement to plane in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp3d.infrastructure.placement import (
        Placement,
    )
    from ospf_python.framework.bpp3d.infrastructure.projection import (
        Projection,
    )


@dataclass(frozen=True)
class PlacementPlaneMapping:
    """放置平面映射。

    将三维放置映射到二维投影平面。
    Maps 3D placement to 2D projection plane.

    Attributes:
        placement: 放置位置 / Placement.
        projection: 投影 / Projection.
        plane: 投影平面名称 / Projection plane name.
    """

    placement: Placement
    """放置位置 / Placement."""

    projection: Projection
    """投影 / Projection."""

    plane: str = "xy"
    """投影平面名称，默认 xy / Plane name, default xy."""

    @staticmethod
    def create(
        *,
        placement: Placement,
        projection: Projection,
        plane: str = "xy",
    ) -> PlacementPlaneMapping:
        """创建映射 / Create mapping.

        Args:
            placement: 放置位置 / Placement.
            projection: 投影 / Projection.
            plane: 平面名称，默认 xy / Plane, default xy.

        Returns:
            放置平面映射实例 / PlacementPlaneMapping.
        """
        return PlacementPlaneMapping(
            placement=placement,
            projection=projection,
            plane=plane,
        )
