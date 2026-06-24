"""矩形类型。

Rectangle type.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.geometry.point import Point


@dataclass(frozen=True)
class Rectangle:
    """二维矩形，由原点和尺寸定义。

    2D rectangle defined by origin and dimensions.

    Attributes:
        origin: 左下角原点。/ Bottom-left origin.
        width: 宽度。/ Width.
        height: 高度。/ Height.
    """

    origin: Point
    width: float
    height: float

    def area(self) -> float:
        """计算面积。

        Compute area.

        Returns:
            矩形面积。/ Rectangle area.
        """
        return self.width * self.height

    def contains(self, point: Point) -> bool:
        """检查点是否在矩形内（含边界）。

        Check whether point is inside the rectangle
        (inclusive of boundary).

        Args:
            point: 待检查的点。/ Point to check.

        Returns:
            是否在矩形内。/ Whether inside the rectangle.
        """
        return (
            self.origin.x <= point.x <= self.origin.x + self.width
            and self.origin.y <= point.y <= self.origin.y + self.height
        )
