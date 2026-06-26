"""Service cost objective — 服务路由代价目标。

计算和汇总所有服务的路由代价，用于最小化总代价。
Computes and aggregates routing costs for all services,
used to minimize total routing cost.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..aggregation import RouteAggregation


@dataclass(frozen=True)
class ServiceCost:
    """单条服务代价 / Per-service cost.

    Attributes:
        service_id: 服务标识 / Service identifier.
        path_cost: 路径单位代价 / Per-unit path cost.
        demand: 服务需求量 / Service demand.
        total_cost: 总代价（路径代价 * 需求量） /
            Total cost (path cost * demand).
    """

    service_id: str
    path_cost: float
    demand: float
    total_cost: float


@dataclass(frozen=True)
class ServiceCostObjective:
    """服务路由代价目标 / Service routing cost objective.

    汇聚所有服务的路由代价，提供总代价计算和按服务
    分解代价的功能。用于最小化总路由代价的优化目标。
    Aggregates routing costs for all services, providing
    total cost computation and per-service cost breakdown.
    Used as the optimization objective to minimize total
    routing cost.

    Attributes:
        objective_name: 目标名称 / Objective name.
    """

    objective_name: str = "min_total_routing_cost"

    def build_costs(
        self,
        aggregation: RouteAggregation,
    ) -> tuple[ServiceCost, ...]:
        """构建每条服务的代价明细。

        Build per-service cost breakdown.

        对每条已分配路由的服务，根据路径边代价和需求量
        计算总代价。
        For each service with an assigned route, computes total
        cost from path edge costs and demand.

        Args:
            aggregation: 路由聚合 / Route aggregation.

        Returns:
            服务代价元组 / Tuple of service costs.
        """
        graph = aggregation.graph
        edge_costs: dict[tuple[str, str], float] = {}
        for edge in graph.edges:
            edge_costs[(edge.source, edge.target)] = edge.cost

        results: list[ServiceCost] = []
        for assignment in aggregation.assignments:
            service = aggregation.get_service(assignment.service_id)
            demand = service.demand if service else 1.0

            # 计算路径上各边的单位代价之和
            # Sum per-unit edge costs along the path
            path_cost = 0.0
            edges = assignment.edge_sequence()
            for src, tgt in edges:
                path_cost += edge_costs.get((src, tgt), 1.0)

            results.append(
                ServiceCost(
                    service_id=assignment.service_id,
                    path_cost=path_cost,
                    demand=demand,
                    total_cost=path_cost * demand,
                )
            )

        return tuple(results)

    def total_cost(self, aggregation: RouteAggregation) -> float:
        """计算总路由代价。

        Compute total routing cost.

        Args:
            aggregation: 路由聚合 / Route aggregation.

        Returns:
            所有服务路由代价之和。
            Sum of all service routing costs.
        """
        return sum(c.total_cost for c in self.build_costs(aggregation))

    def cost_for_service(
        self,
        aggregation: RouteAggregation,
        service_id: str,
    ) -> float:
        """获取指定服务的路由代价。

        Get routing cost for a specific service.

        Args:
            aggregation: 路由聚合 / Route aggregation.
            service_id: 服务标识 / Service identifier.

        Returns:
            服务路由代价，未找到时返回 0.0。
            Service routing cost, or 0.0 if not found.
        """
        for cost in self.build_costs(aggregation):
            if cost.service_id == service_id:
                return cost.total_cost
        return 0.0

    def most_expensive_service(
        self,
        aggregation: RouteAggregation,
    ) -> ServiceCost | None:
        """获取代价最高的服务。

        Get the most expensive service.

        Args:
            aggregation: 路由聚合 / Route aggregation.

        Returns:
            代价最高的服务，无分配时返回 None。
            Most expensive service, or None if no assignments.
        """
        costs = self.build_costs(aggregation)
        if not costs:
            return None
        return max(costs, key=lambda c: c.total_cost)
