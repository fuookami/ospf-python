"""容量数据结构 / Capacity data structure.

表示容器的容量约束。
Represents container capacity constraints.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Capacity:
    """容量 / Capacity.

    描述容器在各维度上的容量限制。
    Describes capacity limits of a container along each
    dimension.

    Attributes:
        width: 宽度容量 / The width capacity.
        height: 高度容量 / The height capacity.
        depth: 深度容量 / The depth capacity.
        weight: 重量容量 / The weight capacity.
    """

    width: float = 0.0
    height: float = 0.0
    depth: float = 0.0
    weight: float = float("inf")
