"""三维坐标轴枚举。

Three-dimensional axis enumeration.
"""

from __future__ import annotations

import enum


class Axis3(enum.Enum):
    """三维坐标轴。

    Three-dimensional coordinate axis.

    Attributes:
        X: X 轴。/ X axis.
        Y: Y 轴。/ Y axis.
        Z: Z 轴。/ Z axis.
    """

    X = "x"
    Y = "y"
    Z = "z"

    @property
    def index(self) -> int:
        """轴索引。/ Axis index."""
        if self is Axis3.X:
            return 0
        if self is Axis3.Y:
            return 1
        return 2
