"""三维坐标平面枚举。

Three-dimensional coordinate plane enumeration.
"""

from __future__ import annotations

import enum


class AxisPlane3(enum.Enum):
    """三维坐标平面。

    Three-dimensional coordinate plane.

    Attributes:
        XY: XY 平面。/ XY plane.
        XZ: XZ 平面。/ XZ plane.
        YZ: YZ 平面。/ YZ plane.
    """

    XY = "xy"
    XZ = "xz"
    YZ = "yz"
