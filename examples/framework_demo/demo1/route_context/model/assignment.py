"""Assignment and Edge models — 路由分配与网络边。

定义路由分配决策和网络边模型。
Defines routing assignment decisions and network edge models.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Edge:
    """网络边 / Network edge.

    表示网络中的一条有向边，连接源节点和目标节点，
    具有传输代价。
    Represents a directed edge in the network, connecting
    a source node to a target node with a transmission cost.

    Attributes:
        edge_id: 边标识 / Edge identifier.
        source: 源节点 / Source node.
        target: 目标节点 / Target node.
        cost: 传输代价 / Transmission cost.
    """

    edge_id: str
    source: str
    target: str
    cost: float = 1.0


@dataclass(frozen=True)
class Assignment:
    """路由分配 / Route assignment.

    表示一条服务的路由分配决策，记录服务所经过的路径
    及其总代价。
    Represents a routing assignment decision for a service,
    recording the path taken and its total cost.

    Attributes:
        service_id: 服务标识 / Service identifier.
        path: 路径节点序列 / Sequence of nodes in the path.
        cost: 路径总代价 / Total path cost.
    """

    service_id: str
    path: tuple[str, ...]
    cost: float = 0.0

    @property
    def hop_count(self) -> int:
        """路径跳数 / Number of hops in the path."""
        return max(0, len(self.path) - 1)

    @property
    def is_valid(self) -> bool:
        """路径是否有效（至少包含起点和终点）。

        Whether the path is valid (contains at least source and target).
        """
        return len(self.path) >= 2

    def edge_sequence(self) -> tuple[tuple[str, str], ...]:
        """获取路径的边序列。

        Get the edge sequence of the path.

        Returns:
            (source, target) 对的元组。
            Tuple of (source, target) pairs.
        """
        return tuple(
            (self.path[i], self.path[i + 1]) for i in range(len(self.path) - 1)
        )
