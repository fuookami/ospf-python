"""圆类型。

Circle type.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.geometry.point import Point


@dataclass(frozen=True)
class Circle:
    """圆，不可变。

    Immutable circle.

    Attributes:
        center: 圆心。/ Center point.
        radius: 半径。/ Radius.
    """

    center: Point
    radius: float

    def area(self) -> float:
        """计算面积。

        Compute area.

        Returns:
            圆面积。/ Circle area.
        """
        return math.pi * self.radius * self.radius

    def circumference(self) -> float:
        """计算周长。

        Compute circumference.

        Returns:
            圆周长。/ Circle circumference.
        """
        return 2.0 * math.pi * self.radius

    def contains(self, point: Point) -> bool:
        """检查点是否在圆内（含边界）。

        Check whether the point is inside the circle
        (inclusive of boundary).

        Args:
            point: 待检查的点。/ Point to check.

        Returns:
            是否在圆内。/ Whether inside the circle.
        """
        dx = point.x - self.center.x
        dy = point.y - self.center.y
        return (dx * dx + dy * dy) <= self.radius * self.radius
