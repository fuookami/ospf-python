"""距离计算函数。

Distance calculation functions.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.geometry.point import Point, Point3


def distance(p1: Point, p2: Point) -> float:
    """计算两点间欧氏距离。

    Compute Euclidean distance between two 2D points.

    Args:
        p1: 第一个点。/ First point.
        p2: 第二个点。/ Second point.

    Returns:
        欧氏距离。/ Euclidean distance.
    """
    return math.hypot(p1.x - p2.x, p1.y - p2.y)


def distance_squared(p1: Point, p2: Point) -> float:
    """计算两点间距离的平方（避免开方）。

    Compute squared distance between two 2D points.

    Args:
        p1: 第一个点。/ First point.
        p2: 第二个点。/ Second point.

    Returns:
        距离的平方。/ Squared distance.
    """
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    return dx * dx + dy * dy


def manhattan_distance(p1: Point, p2: Point) -> float:
    """计算曼哈顿距离。

    Compute Manhattan distance between two 2D points.

    Args:
        p1: 第一个点。/ First point.
        p2: 第二个点。/ Second point.

    Returns:
        曼哈顿距离。/ Manhattan distance.
    """
    return abs(p1.x - p2.x) + abs(p1.y - p2.y)


def distance3(p1: Point3, p2: Point3) -> float:
    """计算三维点间欧氏距离。

    Compute Euclidean distance between two 3D points.

    Args:
        p1: 第一个点。/ First point.
        p2: 第二个点。/ Second point.

    Returns:
        欧氏距离。/ Euclidean distance.
    """
    return math.dist(
        (p1.x, p1.y, p1.z),
        (p2.x, p2.y, p2.z),
    )
