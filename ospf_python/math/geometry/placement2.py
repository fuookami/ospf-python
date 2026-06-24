"""二维放置类型。

2D placement type with position and rotation.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.math.geometry.point import Point


@dataclass(frozen=True)
class Placement2:
    """二维放置（位置 + 旋转角）。

    2D placement (position + rotation angle).

    Attributes:
        position: 位置。/ Position point.
        rotation: 旋转角（弧度）。/ Rotation in radians.
    """

    position: Point
    rotation: float

    @staticmethod
    def identity() -> Placement2:
        """单位放置（原点，零旋转）。/ Identity placement."""
        return Placement2(
            position=Point(x=0.0, y=0.0),
            rotation=0.0,
        )
