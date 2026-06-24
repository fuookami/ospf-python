"""三角剖分工具。

Triangulation utilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ospf_python.math.geometry.triangle import Triangle

if TYPE_CHECKING:
    from ospf_python.math.geometry.point import Point


def triangulate(points: list[Point]) -> list[Triangle]:
    """对点集进行扇形三角剖分。

    Perform fan triangulation on a point set.

    以第一个点为扇心，依次连接后续点对形成三角形。
    使用第一个点 as fan center, connecting
    successive pairs of remaining points.

    Args:
        points: 输入点集。/ Input points.

    Returns:
        三角形列表。/ List of triangles.
    """
    if len(points) < 3:
        return []
    center = points[0]
    result: list[Triangle] = []
    for i in range(1, len(points) - 1):
        tri = Triangle(
            v1=center,
            v2=points[i],
            v3=points[i + 1],
        )
        result.append(tri)
    return result
