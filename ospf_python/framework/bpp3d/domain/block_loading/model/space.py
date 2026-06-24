"""空间数据结构 / Space data structure.

表示三维装箱中的可用空间。
Represents available space in 3D bin packing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Space:
    """空间 / Space.

    用位置和尺寸表示三维空间中的一个区域。
    Represents a region in 3D space using position and dimensions.

    Attributes:
        x: x 坐标 / The x coordinate.
        y: y 坐标 / The y coordinate.
        z: z 坐标 / The z coordinate.
        width: 宽度 / The width.
        height: 高度 / The height.
        depth: 深度 / The depth.
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    width: float = 0.0
    height: float = 0.0
    depth: float = 0.0
