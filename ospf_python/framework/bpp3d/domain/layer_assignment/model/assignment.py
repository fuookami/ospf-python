"""分配数据结构 / Assignment data structure.

表示层到容器的分配关系。
Represents the assignment relationship from layer to container.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Assignment:
    """分配 / Assignment.

    记录一层被分配到哪个容器及其数量。
    Records which container a layer is assigned to and its
    quantity.

    Attributes:
        layer_id: 层标识 / The layer identifier.
        container_id: 容器标识 / The container identifier.
        quantity: 分配数量 / The assigned quantity.
    """

    layer_id: str = ""
    container_id: str = ""
    quantity: int = 0
