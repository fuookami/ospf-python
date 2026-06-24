"""圆柱体类型。

Cylinder type.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.geometry.point import Point3


@dataclass(frozen=True)
class Cylinder3:
    """三维圆柱体，底面中心和高。

    3D cylinder with base center and height.

    Attributes:
        center: 底面中心。/ Base center point.
        radius: 底面半径。/ Base radius.
        height: 高度。/ Height.
    """

    center: Point3
    radius: float
    height: float

    def volume(self) -> float:
        """计算体积。

        Compute volume.

        Returns:
            圆柱体体积。/ Cylinder volume.
        """
        return math.pi * self.radius * self.radius * self.height
