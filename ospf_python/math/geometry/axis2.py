"""二维坐标轴枚举。

Two-dimensional axis enumeration.
"""

from __future__ import annotations

import enum


class Axis2(enum.Enum):
    """二维坐标轴。

    Two-dimensional coordinate axis.

    Attributes:
        X: X 轴。/ X axis.
        Y: Y 轴。/ Y axis.
    """

    X = "x"
    Y = "y"

    @property
    def index(self) -> int:
        """轴索引。/ Axis index."""
        if self is Axis2.X:
            return 0
        return 1

    def other(self) -> Axis2:
        """获取另一轴。/ Get the other axis."""
        if self is Axis2.X:
            return Axis2.Y
        return Axis2.X
