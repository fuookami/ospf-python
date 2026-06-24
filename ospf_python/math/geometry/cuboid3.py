"""长方体类型。

Cuboid type for 3D rectangular boxes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.geometry.point import Point3


@dataclass(frozen=True)
class Cuboid3:
    """三维长方体，由原点和尺寸定义。

    3D cuboid defined by origin and dimensions.

    Attributes:
        origin: 原点（最小角）。/ Origin (minimum corner).
        width: X 方向宽度。/ Width along X.
        height: Y 方向高度。/ Height along Y.
        depth: Z 方向深度。/ Depth along Z.
    """

    origin: Point3
    width: float
    height: float
    depth: float

    def volume(self) -> float:
        """计算体积。

        Compute volume.

        Returns:
            长方体体积。/ Cuboid volume.
        """
        return self.width * self.height * self.depth

    def contains(self, point: Point3) -> bool:
        """检查点是否在长方体内（含边界）。

        Check whether the point is inside the cuboid
        (inclusive of boundary).

        Args:
            point: 待检查的点。/ Point to check.

        Returns:
            是否在长方体内。/ Whether inside the cuboid.
        """
        return (
            self.origin.x <= point.x <= self.origin.x + self.width
            and self.origin.y <= point.y <= self.origin.y + self.height
            and self.origin.z <= point.z <= self.origin.z + self.depth
        )
