"""三角形类型。

Triangle type.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.geometry.point import Point


@dataclass(frozen=True)
class Triangle:
    """二维三角形。

    2D triangle defined by three vertices.

    Attributes:
        v1: 第一个顶点。/ First vertex.
        v2: 第二个顶点。/ Second vertex.
        v3: 第三个顶点。/ Third vertex.
    """

    v1: Point
    v2: Point
    v3: Point

    def area(self) -> float:
        """计算面积（叉积法）。

        Compute area using cross product method.

        Returns:
            三角形面积。/ Triangle area.
        """
        cross = (self.v2.x - self.v1.x) * (self.v3.y - self.v1.y) - (
            self.v3.x - self.v1.x
        ) * (self.v2.y - self.v1.y)
        return abs(cross) / 2.0

    def contains(self, point: Point) -> bool:
        """检查点是否在三角形内（含边界）。

        Check whether point is inside the triangle
        (inclusive of boundary).

        使用重心坐标法。
        Uses barycentric coordinate method.

        Args:
            point: 待检查的点。/ Point to check.

        Returns:
            是否在三角形内。/ Whether inside the triangle.
        """
        d1 = _sign(point, self.v1, self.v2)
        d2 = _sign(point, self.v2, self.v3)
        d3 = _sign(point, self.v3, self.v1)
        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        return not (has_neg and has_pos)


def _sign(p1: Point, p2: Point, p3: Point) -> float:
    """计算叉积符号。/ Compute cross product sign."""
    return (p1.x - p3.x) * (p2.y - p3.y) - (p2.x - p3.x) * (p1.y - p3.y)
