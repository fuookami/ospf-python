"""Route aggregation — 路由聚合。

汇聚路由上下文中的图拓扑、服务列表和分配决策。
Aggregates graph topology, service list, and assignment
decisions from the route context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .model.graph import Graph

if TYPE_CHECKING:
    from .model.assignment import Assignment
    from .model.service import Service


@dataclass(frozen=True)
class RouteAggregation:
    """路由聚合 / Route aggregation.

    将路由域的核心数据——网络图、服务需求和路由分配——
    聚合到一个不可变容器中，供约束构建和目标计算使用。
    Aggregates the core route domain data — network graph,
    service demands, and route assignments — into a single
    immutable container for constraint building and
    objective computation.

    Attributes:
        graph: 网络拓扑图 / Network topology graph.
        services: 服务需求元组 / Tuple of service demands.
        assignments: 路由分配元组 / Tuple of route assignments.
    """

    graph: Graph = field(default_factory=Graph)
    services: tuple[Service, ...] = ()
    assignments: tuple[Assignment, ...] = ()

    # ==================== 不变更新 / Immutable updates =======

    def with_graph(self, graph: Graph) -> RouteAggregation:
        """创建包含新图的聚合副本。

        Copy with a new graph.

        Args:
            graph: 网络拓扑图 / Network topology graph.

        Returns:
            更新后的聚合副本 / Updated aggregation copy.
        """
        return RouteAggregation(
            graph=graph,
            services=self.services,
            assignments=self.assignments,
        )

    def with_service(self, service: Service) -> RouteAggregation:
        """创建包含新服务的聚合副本。

        Copy with a new service appended.

        Args:
            service: 服务需求 / Service demand.

        Returns:
            更新后的聚合副本 / Updated aggregation copy.
        """
        return RouteAggregation(
            graph=self.graph,
            services=(*self.services, service),
            assignments=self.assignments,
        )

    def with_assignment(self, assignment: Assignment) -> RouteAggregation:
        """创建包含新分配的聚合副本。

        Copy with a new assignment appended.

        Args:
            assignment: 路由分配 / Route assignment.

        Returns:
            更新后的聚合副本 / Updated aggregation copy.
        """
        return RouteAggregation(
            graph=self.graph,
            services=self.services,
            assignments=(*self.assignments, assignment),
        )

    # ==================== 查询 / Queries =====================

    def get_service(self, service_id: str) -> Service | None:
        """按标识查找服务。

        Find a service by its identifier.

        Args:
            service_id: 服务标识 / Service identifier.

        Returns:
            匹配的服务，不存在时返回 None。
            Matching service, or None if not found.
        """
        for svc in self.services:
            if svc.service_id == service_id:
                return svc
        return None

    def get_assignment(self, service_id: str) -> Assignment | None:
        """按服务标识查找分配。

        Find an assignment by service identifier.

        Args:
            service_id: 服务标识 / Service identifier.

        Returns:
            匹配的分配，不存在时返回 None。
            Matching assignment, or None if not found.
        """
        for a in self.assignments:
            if a.service_id == service_id:
                return a
        return None

    def assigned_service_ids(self) -> frozenset[str]:
        """获取已分配的服务标识集合。

        Get the set of assigned service identifiers.

        Returns:
            已分配服务标识的冻结集合。
            Frozen set of assigned service identifiers.
        """
        return frozenset(a.service_id for a in self.assignments)

    def unassigned_services(self) -> tuple[Service, ...]:
        """获取尚未分配路由的服务。

        Get services that have not yet been assigned a route.

        Returns:
            未分配服务元组 / Tuple of unassigned services.
        """
        assigned = self.assigned_service_ids()
        return tuple(s for s in self.services if s.service_id not in assigned)

    def total_cost(self) -> float:
        """计算所有分配的总代价。

        Compute the total cost of all assignments.

        Returns:
            总代价 / Total cost.
        """
        return sum(a.cost for a in self.assignments)

    def service_ids(self) -> tuple[str, ...]:
        """获取所有服务标识。

        Get all service identifiers.

        Returns:
            服务标识元组 / Tuple of service identifiers.
        """
        return tuple(s.service_id for s in self.services)
