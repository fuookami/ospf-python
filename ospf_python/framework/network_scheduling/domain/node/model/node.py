"""节点模型 / Node model.

定义网络节点的核心数据结构。
Defines the core data structure for network nodes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ospf_python.framework.network_scheduling.domain.node.model.node_type import (
    NodeType,
)


@dataclass(frozen=True)
class Node:
    """网络节点 / Network node.

    表示网络图中的一个顶点，包含位置、类型和容量信息。
    Represents a vertex in a network graph, containing
    position, type, and capacity information.

    Attributes:
        node_key: 节点唯一标识 / Unique node identifier.
        name: 节点名称 / Node name.
        node_type: 节点类型 / Node type.
        capacity: 节点容量，inf 表示无限制 /
            Node capacity, inf means unlimited.
        x: X 坐标 / X coordinate.
        y: Y 坐标 / Y coordinate.
    """

    node_key: str
    name: str
    node_type: NodeType = NodeType.TRANSIT
    capacity: float = float("inf")
    x: float = 0.0
    y: float = 0.0

    @staticmethod
    def create(
        *,
        node_key: str,
        name: str,
        node_type: NodeType = NodeType.TRANSIT,
        capacity: float = float("inf"),
        x: float = 0.0,
        y: float = 0.0,
    ) -> Node:
        """工厂方法创建节点 / Factory method to create a node.

        Args:
            node_key: 节点唯一标识 / Unique node identifier.
            name: 节点名称 / Node name.
            node_type: 节点类型 / Node type.
            capacity: 节点容量 / Node capacity.
            x: X 坐标 / X coordinate.
            y: Y 坐标 / Y coordinate.

        Returns:
            新的节点实例 / New node instance.
        """
        return Node(
            node_key=node_key,
            name=name,
            node_type=node_type,
            capacity=capacity,
            x=x,
            y=y,
        )

    @property
    def is_source(self) -> bool:
        """是否为源节点 / Whether this is a source node.

        Returns:
            是否为源节点 / Whether source.
        """
        return self.node_type is NodeType.SOURCE

    @property
    def is_sink(self) -> bool:
        """是否为汇节点 / Whether this is a sink node.

        Returns:
            是否为汇节点 / Whether sink.
        """
        return self.node_type is NodeType.SINK

    @property
    def is_transit(self) -> bool:
        """是否为转运节点 / Whether this is a transit node.

        Returns:
            是否为转运节点 / Whether transit.
        """
        return self.node_type is NodeType.TRANSIT

    def distance_to(self, other: Node) -> float:
        """计算到另一节点的欧氏距离。

        Calculate Euclidean distance to another node.

        Args:
            other: 另一节点 / The other node.

        Returns:
            两点间的欧氏距离 / Euclidean distance between
            the two nodes.
        """
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)
