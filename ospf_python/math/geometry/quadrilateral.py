"""四边形类型。

Quadrilateral type.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.geometry.point import Point


@dataclass(frozen=True)
class Quadrilateral:
    """二维四边形，由四个顶点定义。

    2D quadrilateral defined by four vertices.

    Attributes:
        v1: 第一个顶点。/ First vertex.
        v2: 第二个顶点。/ Second vertex.
        v3: 第三个顶点。/ Third vertex.
        v4: 第四个顶点。/ Fourth vertex.
    """

    v1: Point
    v2: Point
    v3: Point
    v4: Point

    def area(self) -> float:
        """计算面积（鞋带公式）。

        Compute area using the shoelace formula.

        Returns:
            四边形面积。/ Quadrilateral area.
        """
        cross1 = (self.v2.x - self.v1.x) * (self.v2.y + self.v1.y)
        cross2 = (self.v3.x - self.v2.x) * (self.v3.y + self.v2.y)
        cross3 = (self.v4.x - self.v3.x) * (self.v4.y + self.v3.y)
        cross4 = (self.v1.x - self.v4.x) * (self.v1.y + self.v4.y)
        return abs(cross1 + cross2 + cross3 + cross4) / 2.0
