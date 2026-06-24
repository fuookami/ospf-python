"""二维点和三维点类型。

2D point and 3D point types.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    """二维点，不可变。

    Immutable 2D point.

    Attributes:
        x: X 坐标。/ X coordinate.
        y: Y 坐标。/ Y coordinate.
    """

    x: float
    y: float

    def __repr__(self) -> str:
        """字符串表示。/ String representation."""
        return f"Point({self.x}, {self.y})"


@dataclass(frozen=True)
class Point3:
    """三维点，不可变。

    Immutable 3D point.

    Attributes:
        x: X 坐标。/ X coordinate.
        y: Y 坐标。/ Y coordinate.
        z: Z 坐标。/ Z coordinate.
    """

    x: float
    y: float
    z: float

    def __repr__(self) -> str:
        """字符串表示。/ String representation."""
        return f"Point3({self.x}, {self.y}, {self.z})"
