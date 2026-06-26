"""带宽上下文 / Bandwidth context.

管理网络路由规划的运行时上下文和注册表。
Manages the runtime context and registry for network routing planning.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from examples.framework_demo.demo1.bandwidth_context.aggregation import (
    BandwidthAggregation,
    Edge,
    Node,
    Service,
)


@dataclass(frozen=True)
class BandwidthContext:
    """带宽上下文 / Bandwidth context.

    作为带宽域对应用层暴露的建模入口，管理边注册表、
    节点注册表、服务注册表和聚合状态。
    Serves as the modeling entry point exposed to the application
    layer, managing edge registry, node registry, service registry,
    and aggregation state.

    Attributes:
        aggregation: 带宽聚合 / Bandwidth aggregation.
        edges: 已注册边 / Registered edges.
        nodes: 已注册节点 / Registered nodes.
        services: 已注册服务 / Registered services.
    """

    aggregation: BandwidthAggregation = field(
        default_factory=BandwidthAggregation,
    )
    """带宽聚合 / Bandwidth aggregation."""

    edges: tuple[Edge, ...] = field(
        default_factory=tuple,
    )
    """已注册边 / Registered edges."""

    nodes: tuple[Node, ...] = field(
        default_factory=tuple,
    )
    """已注册节点 / Registered nodes."""

    services: tuple[Service, ...] = field(
        default_factory=tuple,
    )
    """已注册服务 / Registered services."""

    # ==================== 注册 / Registration =====================

    def register_edge(
        self,
        edge: Edge,
    ) -> BandwidthContext:
        """注册网络边。

        Register a network edge.

        Args:
            edge: 待注册的边。/ Edge to register.

        Returns:
            包含新边的上下文副本。
            A new context with the edge registered.
        """
        return BandwidthContext(
            aggregation=self.aggregation.with_edge(edge),
            edges=self.edges + (edge,),
            nodes=self.nodes,
            services=self.services,
        )

    def register_node(
        self,
        node: Node,
    ) -> BandwidthContext:
        """注册网络节点。

        Register a network node.

        Args:
            node: 待注册的节点。/ Node to register.

        Returns:
            包含新节点的上下文副本。
            A new context with the node registered.
        """
        return BandwidthContext(
            aggregation=self.aggregation.with_node(node),
            edges=self.edges,
            nodes=self.nodes + (node,),
            services=self.services,
        )

    def register_service(
        self,
        service: Service,
    ) -> BandwidthContext:
        """注册带宽服务。

        Register a bandwidth service.

        Args:
            service: 待注册的服务。/ Service to register.

        Returns:
            包含新服务的上下文副本。
            A new context with the service registered.
        """
        return BandwidthContext(
            aggregation=self.aggregation.with_service(service),
            edges=self.edges,
            nodes=self.nodes,
            services=self.services + (service,),
        )

    # ==================== 查询 / Queries =========================

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

    def edges_between(
        self,
        source: str,
        target: str,
    ) -> tuple[Edge, ...]:
        """查找两个节点之间的所有边。

        Find all edges between two nodes.

        Args:
            source: 源节点标识。/ Source node identifier.
            target: 目标节点标识。/ Target node identifier.

        Returns:
            匹配的边元组。/ Tuple of matching edges.
        """
        return tuple(e for e in self.edges if e.source == source and e.target == target)

    def services_for_pair(
        self,
        source: str,
        target: str,
    ) -> tuple[Service, ...]:
        """查找指定源目标节点对的所有服务。

        Find all services for a specific source-target pair.

        Args:
            source: 源节点标识。/ Source node identifier.
            target: 目标节点标识。/ Target node identifier.

        Returns:
            匹配的服务元组。/ Tuple of matching services.
        """
        return tuple(
            s for s in self.services if s.source == source and s.target == target
        )

    # ==================== 统计 / Statistics ========================

    @property
    def total_registered_capacity(self) -> float:
        """已注册边的总容量。

        Total capacity of registered edges.

        Returns:
            所有注册边的容量之和。
            Sum of all registered edge capacities.
        """
        return sum(e.capacity for e in self.edges)

    @property
    def total_registered_demand(self) -> float:
        """已注册服务的总需求。

        Total demand of registered services.

        Returns:
            所有注册服务的需求之和。
            Sum of all registered service demands.
        """
        return sum(s.demand for s in self.services)

    @property
    def transfer_node_count(self) -> int:
        """中转节点数量。

        Number of transfer nodes.

        Returns:
            已注册的中转节点个数。
            Count of registered transfer nodes.
        """
        return sum(1 for n in self.nodes if n.is_transfer)

    def remaining_edge_capacity(
        self,
        edge_id: str,
        used: float = 0.0,
    ) -> float:
        """计算指定边的剩余容量。

        Calculate remaining capacity for an edge.

        Args:
            edge_id: 边标识。/ Edge identifier.
            used: 已使用量。/ Used amount.

        Returns:
            剩余容量，边不存在时返回 0.0。
            Remaining capacity, or 0.0 if edge not found.
        """
        edge = self.edge_by_id(edge_id)
        if edge is None:
            return 0.0
        return max(0.0, edge.capacity - used)
