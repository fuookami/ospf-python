"""三维平面参考框架。

3D plane frame with origin and normal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.geometry.point import Point3


@dataclass(frozen=True)
class PlaneFrame3:
    """三维平面参考框架。

    3D plane reference frame.

    Attributes:
        origin: 原点。/ Origin point.
        normal: 法向量。/ Normal vector (as Point3).
    """

    origin: Point3
    normal: Point3
