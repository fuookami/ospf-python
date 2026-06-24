"""放置位置 / Placement.

BPP3D 中物品的放置位置和方向。
Item placement position and orientation in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.framework.bpp3d.infrastructure.orientation import (
    Orientation,
)


@dataclass(frozen=True)
class Placement:
    """放置位置 / Placement.

    描述物品在容器中的三维坐标和放置方向。
    Describes the 3D coordinates and placement orientation
    of an item in a container.

    Attributes:
        x: X 坐标 / X coordinate.
        y: Y 坐标 / Y coordinate.
        z: Z 坐标 / Z coordinate.
        orientation: 放放方向 / Placement orientation.
    """

    x: float
    """X 坐标 / X coordinate."""

    y: float
    """Y 坐标 / Y coordinate."""

    z: float
    """Z 坐标 / Z coordinate."""

    orientation: Orientation
    """放置方向 / Placement orientation."""

    @staticmethod
    def create(
        *,
        x: float,
        y: float,
        z: float,
        orientation: Orientation = Orientation.XYZ,
    ) -> Placement:
        """创建放置位置 / Create placement.

        Args:
            x: X 坐标 / X coordinate.
            y: Y 坐标 / Y coordinate.
            z: Z 坐标 / Z coordinate.
            orientation: 放置方向，默认 XYZ /
                Placement orientation, default XYZ.

        Returns:
            放置位置实例 / Placement instance.
        """
        return Placement(
            x=x,
            y=y,
            z=z,
            orientation=orientation,
        )
