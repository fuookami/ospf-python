"""带宽聚合 / Bandwidth aggregation.

聚合网络拓扑中的边、节点和服务信息。
Aggregates edge, node, and service information from the network topology.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Edge:
    """网络边 / Network edge.

    表示网络拓扑中的一条链路。
    Represents a link in the network topology.

    Attributes:
        edge_id: 边标识 / Edge identifier.
        source: 源节点标识 / Source node identifier.
        target: 目标节点标识 / Target node identifier.
        capacity: 链路容量 / Link capacity.
        cost_per_unit: 单位带宽成本 / Cost per unit bandwidth.
    """

    edge_id: str = ""
    """边标识 / Edge identifier."""

    source: str = ""
    """源节点标识 / Source node identifier."""

    target: str = ""
    """目标节点标识 / Target node identifier."""

    capacity: float = 0.0
    """链路容量 / Link capacity."""

    cost_per_unit: float = 0.0
    """单位带宽成本 / Cost per unit bandwidth."""


@dataclass(frozen=True)
class Node:
    """网络节点 / Network node.

    表示网络拓扑中的一个节点。
    Represents a node in the network topology.

    Attributes:
        node_id: 节点标识 / Node identifier.
        is_transfer: 是否为中转节点 / Whether it is a transfer node.
        max_bandwidth: 节点最大带宽处理能力 /
            Maximum bandwidth processing capacity.
    """

    node_id: str = ""
    """节点标识 / Node identifier."""

    is_transfer: bool = False
    """是否为中转节点 / Whether it is a transfer node."""

    max_bandwidth: float = 0.0
    """节点最大带宽处理能力 / Maximum bandwidth processing capacity."""


@dataclass(frozen=True)
class Service:
    """网络服务 / Network service.

    表示一条需要路由的带宽服务请求。
    Represents a bandwidth service request to be routed.

    Attributes:
        service_id: 服务标识 / Service identifier.
        source: 源节点标识 / Source node identifier.
        target: 目标节点标识 / Target node identifier.
        demand: 带宽需求 / Bandwidth demand.
        priority: 服务优先级 / Service priority.
    """

    service_id: str = ""
    """服务标识 / Service identifier."""

    source: str = ""
    """源节点标识 / Source node identifier."""

    target: str = ""
    """目标节点标识 / Target node identifier."""

    demand: float = 0.0
    """带宽需求 / Bandwidth demand."""

    priority: int = 0
    """服务优先级 / Service priority."""


@dataclass(frozen=True)
class BandwidthAggregation:
    """带宽聚合 / Bandwidth aggregation.

    汇总网络拓扑中的边、节点和服务信息，提供全局视角的
    容量和需求统计。
    Summarizes edge, node, and service information from the
    network topology, providing a global view of capacity
    and demand statistics.

    Attributes:
        edges: 网络边列表 / Network edge list.
        nodes: 网络节点列表 / Network node list.
        services: 服务列表 / Service list.
    """

    edges: tuple[Edge, ...] = field(
        default_factory=tuple,
    )
    """网络边列表 / Network edge list."""

    nodes: tuple[Node, ...] = field(
        default_factory=tuple,
    )
    """网络节点列表 / Network node list."""

    services: tuple[Service, ...] = field(
        default_factory=tuple,
    )
    """服务列表 / Service list."""

    # ==================== 工厂方法 / Factory Methods ==============

    @staticmethod
    def from_topology(
        edges: tuple[Edge, ...],
        nodes: tuple[Node, ...],
        services: tuple[Service, ...],
    ) -> BandwidthAggregation:
        """从拓扑信息创建聚合。

        Create aggregation from topology information.

        Args:
            edges: 网络边列表。/ Network edge list.
            nodes: 网络节点列表。/ Network node list.
            services: 服务列表。/ Service list.

        Returns:
            聚合实例。/ Aggregation instance.
        """
        return BandwidthAggregation(
            edges=edges,
            nodes=nodes,
            services=services,
        )

    # ==================== 查询 / Queries =========================

    @property
    def total_capacity(self) -> float:
        """总链路容量。

        Total link capacity.

        Returns:
            所有边的容量之和。
            Sum of all edge capacities.
        """
        return sum(e.capacity for e in self.edges)

    @property
    def total_demand(self) -> float:
        """总带宽需求。

        Total bandwidth demand.

        Returns:
            所有服务的需求之和。
            Sum of all service demands.
        """
        return sum(s.demand for s in self.services)

    @property
    def capacity_utilization(self) -> float:
        """容量利用率。

        Capacity utilization ratio.

        Returns:
            总需求除以总容量，无容量时返回 0.0。
            Total demand divided by total capacity,
            or 0.0 if no capacity.
        """
        cap = self.total_capacity
        if cap <= 0.0:
            return 0.0
        return self.total_demand / cap

    @property
    def transfer_nodes(self) -> tuple[Node, ...]:
        """获取所有中转节点。

        Get all transfer nodes.

        Returns:
            中转节点元组。/ Tuple of transfer nodes.
        """
        return tuple(n for n in self.nodes if n.is_transfer)

    def edges_for_node(
        self,
        node_id: str,
    ) -> tuple[Edge, ...]:
        """获取与指定节点关联的所有边。

        Get all edges connected to a specific node.

        Args:
            node_id: 节点标识。/ Node identifier.

        Returns:
            关联的边元组。/ Tuple of connected edges.
        """
        return tuple(
            e for e in self.edges if e.source == node_id or e.target == node_id
        )

    def services_from_node(
        self,
        node_id: str,
    ) -> tuple[Service, ...]:
        """获取从指定节点出发的所有服务。

        Get all services originating from a specific node.

        Args:
            node_id: 节点标识。/ Node identifier.

        Returns:
            服务元组。/ Tuple of services.
        """
        return tuple(s for s in self.services if s.source == node_id)

    def edge_by_id(
        self,
        edge_id: str,
    ) -> Edge | None:
        """按标识查找边。

        Find edge by identifier.

        Args:
            edge_id: 边标识。/ Edge identifier.

        Returns:
            匹配的边，不存在时返回 None。
            Matching edge, or None if not found.
        """
        for edge in self.edges:
            if edge.edge_id == edge_id:
                return edge
        return None

    def node_by_id(
        self,
        node_id: str,
    ) -> Node | None:
        """按标识查找节点。

        Find node by identifier.

        Args:
            node_id: 节点标识。/ Node identifier.

        Returns:
            匹配的节点，不存在时返回 None。
            Matching node, or None if not found.
        """
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None

    def service_by_id(
        self,
        service_id: str,
    ) -> Service | None:
        """按标识查找服务。

        Find service by identifier.

        Args:
            service_id: 服务标识。/ Service identifier.

        Returns:
            匹配的服务，不存在时返回 None。
            Matching service, or None if not found.
        """
        for svc in self.services:
            if svc.service_id == service_id:
                return svc
        return None

    def with_edge(self, edge: Edge) -> BandwidthAggregation:
        """添加边到聚合。

        Add an edge to the aggregation.

        Args:
            edge: 要添加的边。/ Edge to add.

        Returns:
            包含新边的聚合副本。
            A new aggregation with the edge added.
        """
        return BandwidthAggregation(
            edges=self.edges + (edge,),
            nodes=self.nodes,
            services=self.services,
        )

    def with_node(self, node: Node) -> BandwidthAggregation:
        """添加节点到聚合。

        Add a node to the aggregation.

        Args:
            node: 要添加的节点。/ Node to add.

        Returns:
            包含新节点的聚合副本。
            A new aggregation with the node added.
        """
        return BandwidthAggregation(
            edges=self.edges,
            nodes=self.nodes + (node,),
            services=self.services,
        )

    def with_service(self, service: Service) -> BandwidthAggregation:
        """添加服务到聚合。

        Add a service to the aggregation.

        Args:
            service: 要添加的服务。/ Service to add.

        Returns:
            包含新服务的聚合副本。
            A new aggregation with the service added.
        """
        return BandwidthAggregation(
            edges=self.edges,
            nodes=self.nodes,
            services=self.services + (service,),
        )
