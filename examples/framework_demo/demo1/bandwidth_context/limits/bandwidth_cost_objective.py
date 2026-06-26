"""带宽成本目标 / Bandwidth cost objective.

最小化网络路由的总带宽成本。
Minimizes the total bandwidth cost of network routing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostTerm:
    """成本项 / Cost term.

    表示目标函数中一条边的带宽成本项。
    Represents a bandwidth cost term for an edge in the
    objective function.

    Attributes:
        edge_id: 边标识 / Edge identifier.
        allocated_bandwidth: 分配的带宽 / Allocated bandwidth.
        cost_per_unit: 单位成本 / Cost per unit.
        total_cost: 总成本 / Total cost.
    """

    edge_id: str = ""
    """边标识 / Edge identifier."""

    allocated_bandwidth: float = 0.0
    """分配的带宽 / Allocated bandwidth."""

    cost_per_unit: float = 0.0
    """单位成本 / Cost per unit."""

    total_cost: float = 0.0
    """总成本 / Total cost."""


@dataclass(frozen=True)
class BandwidthCostObjective:
    """带宽成本目标 / Bandwidth cost objective.

    构建最小化总带宽成本的目标函数项。遍历所有边的带宽
    分配，计算加权成本并汇总。
    Builds objective function terms for minimizing total bandwidth
    cost. Iterates over all edge bandwidth allocations, computes
    weighted costs and sums them.

    Attributes:
        objective_name: 目标函数名称 / Objective function name.
        cost_multiplier: 成本乘数 / Cost multiplier.
    """

    objective_name: str = "bandwidth_cost"
    """目标函数名称 / Objective function name."""

    cost_multiplier: float = 1.0
    """成本乘数 / Cost multiplier."""

    def build_cost_terms(
        self,
        edge_allocations: dict[str, float],
        edge_costs: dict[str, float],
    ) -> tuple[CostTerm, ...]:
        """构建成本项列表。

        Build cost term list.

        Args:
            edge_allocations: 边到分配带宽的映射。
                / Edge-to-allocated-bandwidth mapping.
            edge_costs: 边到单位成本的映射。
                / Edge-to-unit-cost mapping.

        Returns:
            成本项元组。/ Tuple of cost terms.
        """
        terms: list[CostTerm] = []
        for edge_id, bandwidth in edge_allocations.items():
            if bandwidth <= 0.0:
                continue
            unit_cost = edge_costs.get(edge_id, 0.0)
            terms.append(
                CostTerm(
                    edge_id=edge_id,
                    allocated_bandwidth=bandwidth,
                    cost_per_unit=unit_cost,
                    total_cost=bandwidth * unit_cost * self.cost_multiplier,
                )
            )
        return tuple(terms)

    def calculate_total_cost(
        self,
        edge_allocations: dict[str, float],
        edge_costs: dict[str, float],
    ) -> float:
        """计算总带宽成本。

        Calculate total bandwidth cost.

        Args:
            edge_allocations: 边到分配带宽的映射。
                / Edge-to-allocated-bandwidth mapping.
            edge_costs: 边到单位成本的映射。
                / Edge-to-unit-cost mapping.

        Returns:
            总成本值。/ Total cost value.
        """
        terms = self.build_cost_terms(edge_allocations, edge_costs)
        return sum(t.total_cost for t in terms)

    def cost_breakdown(
        self,
        edge_allocations: dict[str, float],
        edge_costs: dict[str, float],
    ) -> dict[str, float]:
        """生成成本分解报告。

        Generate cost breakdown report.

        Args:
            edge_allocations: 边到分配带宽的映射。
                / Edge-to-allocated-bandwidth mapping.
            edge_costs: 边到单位成本的映射。
                / Edge-to-unit-cost mapping.

        Returns:
            边标识到成本的映射。/ Edge-to-cost mapping.
        """
        terms = self.build_cost_terms(edge_allocations, edge_costs)
        return {t.edge_id: t.total_cost for t in terms}
