"""线段类型。

Edge type connecting two points.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.geometry.point import Point


@dataclass(frozen=True)
class Edge:
    """二维线段。

    2D edge connecting two points.

    Attributes:
        start: 起点。/ Start point.
        end: 终点。/ End point.
    """

    start: Point
    end: Point

    def length(self) -> float:
        """计算线段长度。

        Compute edge length.

        Returns:
            线段长度。/ Edge length.
        """
        import math

        return math.hypot(
            self.end.x - self.start.x,
            self.end.y - self.start.y,
        )
