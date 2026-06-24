"""二维包围盒。

2D axis-aligned bounding box.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.math.geometry.point import Point


@dataclass(frozen=True)
class Box2:
    """二维轴对齐包围盒。

    2D axis-aligned bounding box.

    Attributes:
        min_point: 最小角点。/ Minimum corner point.
        max_point: 最大角点。/ Maximum corner point.
    """

    min_point: Point
    max_point: Point

    def contains(self, point: Point) -> bool:
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
        )

    def area(self) -> float:
        """计算面积。

        Compute area.

        Returns:
            包围盒面积。/ Box area.
        """
        dx = self.max_point.x - self.min_point.x
        dy = self.max_point.y - self.min_point.y
        return dx * dy

    def center(self) -> Point:
        """计算中心点。

        Compute center point.

        Returns:
            包围盒中心。/ Box center.
        """
        return Point(
            x=(self.min_point.x + self.max_point.x) / 2.0,
            y=(self.min_point.y + self.max_point.y) / 2.0,
        )
