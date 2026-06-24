"""三维包围盒。

3D axis-aligned bounding box.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.math.geometry.point import Point3


@dataclass(frozen=True)
class Box3:
    """三维轴对齐包围盒。

    3D axis-aligned bounding box.

    Attributes:
        min_point: 最小角点。/ Minimum corner point.
        max_point: 最大角点。/ Maximum corner point.
    """

    min_point: Point3
    max_point: Point3

    def contains(self, point: Point3) -> bool:
        """检查点是否在包围盒内（含边界）。

        Check whether the point is inside the box
        (inclusive of boundary).

        Args:
            point: 待检查的点。/ Point to check.

        Returns:
            是否在盒内。/ Whether inside the box.
        """
        return (
            self.min_point.x <= point.x <= self.max_point.x
            and self.min_point.y <= point.y <= self.max_point.y
            and self.min_point.z <= point.z <= self.max_point.z
        )

    def volume(self) -> float:
        """计算体积。

        Compute volume.

        Returns:
            包围盒体积。/ Box volume.
        """
        dx = self.max_point.x - self.min_point.x
        dy = self.max_point.y - self.min_point.y
        dz = self.max_point.z - self.min_point.z
        return dx * dy * dz

    def center(self) -> Point3:
        """计算中心点。

        Compute center point.

        Returns:
            包围盒中心。/ Box center.
        """
        return Point3(
            x=(self.min_point.x + self.max_point.x) / 2.0,
            y=(self.min_point.y + self.max_point.y) / 2.0,
            z=(self.min_point.z + self.max_point.z) / 2.0,
        )
