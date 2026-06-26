"""Route context — 路由上下文。

路由域的建模入口，负责管理图拓扑、服务需求和路由分配的
注册与查询。对齐 Kotlin RouteContext 模式。
The modeling entry point for the route domain, responsible
for managing registration and querying of graph topology,
service demands, and route assignments. Aligns with the
Kotlin RouteContext pattern.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .aggregation import RouteAggregation
from .limits.node_assignment_constraint import NodeAssignmentConstraint
from .limits.service_assignment_constraint import ServiceAssignmentConstraint
from .limits.service_cost_objective import ServiceCostObjective

if TYPE_CHECKING:
    from .model.assignment import Assignment
    from .model.graph import Graph
    from .model.service import Service


@dataclass(frozen=True)
class RouteContext:
    """路由上下文 / Route context.

    作为路由域对应用层暴露的建模入口，管理聚合状态。
    提供图注册、服务注册、分配注册及约束/目标构建功能。
    Serves as the modeling entry point exposed to the application
    layer, managing aggregation state. Provides graph registration,
    service registration, assignment registration, and
    constraint/objective building.

    Attributes:
        aggregation: 路由聚合 / Route aggregation.
    """

    aggregation: RouteAggregation = field(
        default_factory=RouteAggregation,
    )

    # ==================== 注册 / Registration ================

    def register_graph(self, graph: Graph) -> RouteContext:
        """注册网络拓扑图。

        Register the network topology graph.

        Args:
            graph: 网络拓扑图 / Network topology graph.

        Returns:
            包含新图的上下文副本。
            A new context with the graph registered.
        """
        return RouteContext(
            aggregation=self.aggregation.with_graph(graph),
        )

    def register_service(self, service: Service) -> RouteContext:
        """注册服务需求。

        Register a service demand.

        Args:
            service: 服务需求 / Service demand.

        Returns:
            包含新服务的上下文副本。
            A new context with the service registered.
        """
        return RouteContext(
            aggregation=self.aggregation.with_service(service),
        )

    def register_assignment(self, assignment: Assignment) -> RouteContext:
        """注册路由分配。

        Register a route assignment.

        Args:
            assignment: 路由分配 / Route assignment.

        Returns:
            包含新分配的上下文副本。
            A new context with the assignment registered.
        """
        return RouteContext(
            aggregation=self.aggregation.with_assignment(assignment),
        )

    # ==================== 查询 / Queries =====================

    def get_graph(self) -> Graph:
        """获取网络拓扑图。

        Get the network topology graph.

        Returns:
            网络拓扑图 / Network topology graph.
        """
        return self.aggregation.graph

    def get_services(self) -> tuple[Service, ...]:
        """获取所有服务需求。

        Get all service demands.

        Returns:
            服务需求元组 / Tuple of service demands.
        """
        return self.aggregation.services

    def get_assignments(self) -> tuple[Assignment, ...]:
        """获取所有路由分配。

        Get all route assignments.

        Returns:
            路由分配元组 / Tuple of route assignments.
        """
        return self.aggregation.assignments

    def get_assignment(self, service_id: str) -> Assignment | None:
        """按服务标识查找分配。

        Find an assignment by service identifier.

        Args:
            service_id: 服务标识 / Service identifier.

        Returns:
            匹配的分配，不存在时返回 None。
            Matching assignment, or None if not found.
        """
        return self.aggregation.get_assignment(service_id)

    def unassigned_services(self) -> tuple[Service, ...]:
        """获取尚未分配路由的服务。

        Get services without an assigned route.

        Returns:
            未分配服务元组 / Tuple of unassigned services.
        """
        return self.aggregation.unassigned_services()

    # ==================== 约束构建 / Constraint building =======

    def check_flow_conservation(self) -> bool:
        """检查流守恒约束。

        Check flow conservation constraints.

        验证每个中间节点的流入量等于流出量，
        源节点净流出等于需求量，目标节点净流入等于需求量。
        Verifies that inflow equals outflow at each intermediate
        node, net outflow at source equals demand, and net inflow
        at target equals demand.

        Returns:
            若所有流守恒约束均满足则返回 True。
            True if all flow conservation constraints are satisfied.
        """
        constraint = NodeAssignmentConstraint()
        return constraint.is_feasible(self.aggregation)

    def check_service_routing(self) -> bool:
        """检查服务路由约束。

        Check service routing constraints.

        验证每条服务是否已被分配有效路由。
        Verifies that each service has been assigned a valid route.

        Returns:
            若所有服务均已路由则返回 True。
            True if all services have been routed.
        """
        constraint = ServiceAssignmentConstraint()
        return constraint.is_feasible(self.aggregation)

    def compute_total_cost(self) -> float:
        """计算路由总代价。

        Compute the total routing cost.

        Returns:
            所有服务路由代价之和。
            Sum of all service routing costs.
        """
        objective = ServiceCostObjective()
        return objective.total_cost(self.aggregation)
