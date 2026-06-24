"""放置工厂 / Placement factory.

BPP3D 中创建放置位置的工厂。
Factory for creating placements in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.framework.bpp3d.infrastructure.orientation import (
    Orientation,
)
from ospf_python.framework.bpp3d.infrastructure.placement import (
    Placement,
)


@dataclass(frozen=True)
class PlacementFactory:
    """放置工厂 / Placement factory.

    提供创建放置位置的便捷方法。
    Provides convenient methods for creating placements.

    Attributes:
        container_width: 容器宽度 / Container width.
        container_height: 容器高度 / Container height.
        container_depth: 容器深度 / Container depth.
    """

    container_width: float
    """容器宽度 / Container width."""

    container_height: float
    """容器高度 / Container height."""

    container_depth: float
    """容器深度 / Container depth."""

    @staticmethod
    def create(
        *,
        container_width: float,
        container_height: float,
        container_depth: float,
    ) -> PlacementFactory:
        """创建工厂 / Create factory.

        Args:
            container_width: 容器宽度 / Container width.
            container_height: 容器高度 / Container height.
            container_depth: 容器深度 / Container depth.

        Returns:
            放置工厂实例 / PlacementFactory instance.
        """
        return PlacementFactory(
            container_width=container_width,
            container_height=container_height,
            container_depth=container_depth,
        )

    def create_origin_placement(
        self,
        *,
        orientation: Orientation = Orientation.XYZ,
    ) -> Placement:
        """创建原点放置 / Create origin placement.

        Args:
            orientation: 放置方向，默认 XYZ /
                Orientation, default XYZ.

        Returns:
            原点放置实例 / Origin placement instance.
        """
        return Placement.create(
            x=0.0,
            y=0.0,
            z=0.0,
            orientation=orientation,
        )
