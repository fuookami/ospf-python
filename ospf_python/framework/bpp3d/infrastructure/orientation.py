"""方向枚举 / Orientation enumeration.

定义 BPP3D 中物品的放置方向。
Defines item placement orientations in BPP3D.
"""

from __future__ import annotations

import enum


class Orientation(enum.Enum):
    """放置方向枚举 / Placement orientation enumeration.

    描述物品在三维空间中的六种可能方向。
    Describes six possible orientations of an item in
    three-dimensional space.

    Attributes:
        XYZ: X-Y-Z 方向 / X-Y-Z orientation.
        XZY: X-Z-Y 方向 / X-Z-Y orientation.
        YXZ: Y-X-Z 方向 / Y-X-Z orientation.
        YZX: Y-Z-X 方向 / Y-Z-X orientation.
        ZXY: Z-X-Y 方向 / Z-X-Y orientation.
        ZYX: Z-Y-X 方向 / Z-Y-X orientation.
    """

    XYZ = "xyz"
    """X-Y-Z 方向 / X-Y-Z orientation."""

    XZY = "xzy"
    """X-Z-Y 方向 / X-Z-Y orientation."""

    YXZ = "yxz"
    """Y-X-Z 方向 / Y-X-Z orientation."""

    YZX = "yzx"
    """Y-Z-X 方向 / Y-Z-X orientation."""

    ZXY = "zxy"
    """Z-X-Y 方向 / Z-X-Y orientation."""

    ZYX = "zyx"
    """Z-Y-X 方向 / Z-Y-X orientation."""
