"""三维放置类型。

3D placement type with position and rotation.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.math.geometry.point import Point3


@dataclass(frozen=True)
class Placement3:
    """三维放置（位置 + 旋转角）。

    3D placement (position + rotation angles).

    Attributes:
        position: 位置。/ Position point.
        rotation_x: X 轴旋转角（弧度）。/ X rotation in radians.
        rotation_y: Y 轴旋转角（弧度）。/ Y rotation in radians.
        rotation_z: Z 轴旋转角（弧度）。/ Z rotation in radians.
    """

    position: Point3
    rotation_x: float
    rotation_y: float
    rotation_z: float

    @staticmethod
    def identity() -> Placement3:
        """单位放置。/ Identity placement."""
        return Placement3(
            position=Point3(x=0.0, y=0.0, z=0.0),
            rotation_x=0.0,
            rotation_y=0.0,
            rotation_z=0.0,
        )
