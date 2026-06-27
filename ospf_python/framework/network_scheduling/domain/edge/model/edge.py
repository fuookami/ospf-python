"""边模型 / Edge model.

定义网络边（弧）的核心数据结构。
Defines the core data structure for network edges (arcs).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Edge:
    """网络边 / Network edge.

    表示网络图中的一条有向边，连接两个节点并携带
    容量、代价和长度属性。
    Represents a directed edge in a network graph,
    connecting two nodes with capacity, cost, and
    length attributes.

    Attributes:
        edge_key: 边唯一标识 / Unique edge identifier.
        from_node_key: 起始节点标识 / Source node identifier.
        to_node_key: 终止节点标识 / Target node identifier.
        capacity: 边容量 / Edge capacity.
        cost: 单位流量代价 / Unit flow cost.
        length: 边长度 / Edge length.
    """

    edge_key: str
    from_node_key: str
    to_node_key: str
    capacity: float = float("inf")
    cost: float = 1.0
    length: float = 0.0

    @staticmethod
    def create(
        *,
        edge_key: str,
        from_node_key: str,
        to_node_key: str,
        capacity: float = float("inf"),
        cost: float = 1.0,
        length: float = 0.0,
    ) -> Edge:
        """工厂方法创建边 / Factory method to create an edge.

        Args:
            edge_key: 边唯一标识 / Unique edge identifier.
            from_node_key: 起始节点标识 / Source node identifier.
            to_node_key: 终止节点标识 / Target node identifier.
            capacity: 边容量 / Edge capacity.
            cost: 单位流量代价 / Unit flow cost.
            length: 边长度 / Edge length.

        Returns:
            新的边实例 / New edge instance.
        """
        return Edge(
            edge_key=edge_key,
            from_node_key=from_node_key,
            to_node_key=to_node_key,
            capacity=capacity,
            cost=cost,
            length=length,
        )

    @property
    def is_reverse_possible(self) -> bool:
        """是否可创建反向边 / Whether a reverse edge is possible.

        无容量限制的边不建议创建反向边。
        Edges with unlimited capacity should not have
        a reverse counterpart created.

        Returns:
            是否可反向 / Whether reverse is possible.
        """
        return self.capacity < float("inf")

    def connects(self, node_key: str) -> bool:
        """检查是否连接指定节点 / Check if connects to a given node.

        Args:
            node_key: 节点标识 / Node identifier.

        Returns:
            该边是否以 node_key 为起点或终点 /
            Whether the edge has node_key as source or target.
        """
        return self.from_node_key == node_key or self.to_node_key == node_key

    def reversed(self) -> Edge:
        """创建反向边 / Create a reversed edge.

        返回方向相反、代价相同的边。容量保持不变。
        Returns an edge with reversed direction and same cost.
        Capacity remains unchanged.

        Returns:
            反向边实例 / Reversed edge instance.
        """
        return Edge(
            edge_key=f"{self.edge_key}_rev",
            from_node_key=self.to_node_key,
            to_node_key=self.from_node_key,
            capacity=self.capacity,
            cost=self.cost,
            length=self.length,
        )

    def effective_cost(self, flow: float) -> float:
        """计算给定流量下的有效代价。

        Calculate the effective cost for a given flow amount.

        当流量超出容量时，代价按超出比例增加。
        When flow exceeds capacity, cost increases
        proportionally.

        Args:
            flow: 流量值 / Flow amount.

        Returns:
            有效代价 / Effective cost.
        """
        if self.capacity <= 0.0 or flow <= self.capacity:
            return self.cost
        overflow_ratio = flow / self.capacity
        return self.cost * overflow_ratio
