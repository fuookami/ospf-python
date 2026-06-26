"""解决方案分析器 / Solution analyzer.

分析网络路由解决方案的质量和可行性。
Analyzes the quality and feasibility of network routing solutions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo1.bandwidth_context.aggregation import (
        BandwidthAggregation,
    )
from examples.framework_demo.demo1.bandwidth_context.limits.bandwidth_cost_objective import (
    BandwidthCostObjective,
)
from examples.framework_demo.demo1.bandwidth_context.limits.demand_constraint import (
    DemandConstraint,
    DemandViolation,
)
from examples.framework_demo.demo1.bandwidth_context.limits.edge_bandwidth_constraint import (
    EdgeBandwidthConstraint,
    EdgeCapacityViolation,
)
from examples.framework_demo.demo1.bandwidth_context.limits.service_capacity_constraint import (
    ServiceCapacityConstraint,
    ServiceCapacityViolation,
)
from examples.framework_demo.demo1.bandwidth_context.limits.transfer_node_bandwidth_constraint import (
    TransferNodeBandwidthConstraint,
    TransferNodeViolation,
)


@dataclass(frozen=True)
class ViolationSummary:
    """违反摘要 / Violation summary.

    汇总所有约束违反的统计信息。
    Summarizes statistics of all constraint violations.

    Attributes:
        demand_violations: 需求违反列表 / Demand violation list.
        edge_violations: 边容量违反列表 /
            Edge capacity violation list.
        service_violations: 服务容量违反列表 /
            Service capacity violation list.
        transfer_node_violations: 中转节点违反列表 /
            Transfer node violation list.
    """

    demand_violations: tuple[DemandViolation, ...] = field(
        default_factory=tuple,
    )
    """需求违反列表 / Demand violation list."""

    edge_violations: tuple[EdgeCapacityViolation, ...] = field(
        default_factory=tuple,
    )
    """边容量违反列表 / Edge capacity violation list."""

    service_violations: tuple[ServiceCapacityViolation, ...] = field(
        default_factory=tuple,
    )
    """服务容量违反列表 / Service capacity violation list."""

    transfer_node_violations: tuple[TransferNodeViolation, ...] = field(
        default_factory=tuple,
    )
    """中转节点违反列表 / Transfer node violation list."""

    @property
    def total_violation_count(self) -> int:
        """总违反数量。

        Total violation count.

        Returns:
            所有约束违反的数量之和。
            Sum of all violation counts.
        """
        return (
            len(self.demand_violations)
            + len(self.edge_violations)
            + len(self.service_violations)
            + len(self.transfer_node_violations)
        )

    @property
    def is_feasible(self) -> bool:
        """是否可行。

        Whether the solution is feasible.

        Returns:
            无任何违反时返回 True。
            True if there are no violations.
        """
        return self.total_violation_count == 0


@dataclass(frozen=True)
class QualityMetrics:
    """质量指标 / Quality metrics.

    衡量解决方案的整体质量。
    Measures the overall quality of a solution.

    Attributes:
        total_cost: 总带宽成本 / Total bandwidth cost.
        capacity_utilization: 容量利用率 / Capacity utilization.
        demand_satisfaction: 需求满足率 / Demand satisfaction rate.
        feasibility_score: 可行性评分 / Feasibility score.
    """

    total_cost: float = 0.0
    """总带宽成本 / Total bandwidth cost."""

    capacity_utilization: float = 0.0
    """容量利用率 / Capacity utilization."""

    demand_satisfaction: float = 0.0
    """需求满足率 / Demand satisfaction rate."""

    feasibility_score: float = 0.0
    """可行性评分 / Feasibility score."""


@dataclass(frozen=True)
class AnalysisResult:
    """分析结果 / Analysis result.

    封装解决方案分析的完整结果。
    Encapsulates the complete result of solution analysis.

    Attributes:
        violation_summary: 违反摘要 / Violation summary.
        quality_metrics: 质量指标 / Quality metrics.
    """

    violation_summary: ViolationSummary = field(
        default_factory=ViolationSummary,
    )
    """违反摘要 / Violation summary."""

    quality_metrics: QualityMetrics = field(
        default_factory=QualityMetrics,
    )
    """质量指标 / Quality metrics."""

    @property
    def is_feasible(self) -> bool:
        """是否可行。

        Whether the solution is feasible.

        Returns:
            无违反时返回 True。
            True if there are no violations.
        """
        return self.violation_summary.is_feasible


@dataclass(frozen=True)
class SolutionAnalyzer:
    """解决方案分析器 / Solution analyzer.

    综合分析网络路由解决方案的可行性和质量。执行所有
    约束检查，收集违反信息，并计算质量指标。
    Comprehensively analyzes the feasibility and quality of a
    network routing solution. Executes all constraint checks,
    collects violations, and computes quality metrics.

    Attributes:
        demand_constraint: 需求约束 / Demand constraint.
        edge_bw_constraint: 边带宽约束 /
            Edge bandwidth constraint.
        svc_cap_constraint: 服务容量约束 /
            Service capacity constraint.
        transfer_node_constraint: 中转节点约束 /
            Transfer node constraint.
        cost_objective: 成本目标 / Cost objective.
    """

    demand_constraint: DemandConstraint = field(
        default_factory=DemandConstraint,
    )
    """需求约束 / Demand constraint."""

    edge_bw_constraint: EdgeBandwidthConstraint = field(
        default_factory=EdgeBandwidthConstraint,
    )
    """边带宽约束 / Edge bandwidth constraint."""

    svc_cap_constraint: ServiceCapacityConstraint = field(
        default_factory=ServiceCapacityConstraint,
    )
    """服务容量约束 / Service capacity constraint."""

    transfer_node_constraint: TransferNodeBandwidthConstraint = field(
        default_factory=TransferNodeBandwidthConstraint,
    )
    """中转节点约束 / Transfer node constraint."""

    cost_objective: BandwidthCostObjective = field(
        default_factory=BandwidthCostObjective,
    )
    """成本目标 / Cost objective."""

    def analyze(
        self,
        *,
        aggregation: BandwidthAggregation,
        edge_allocations: dict[str, float],
        service_allocations: dict[str, float],
        node_throughputs: dict[str, float],
    ) -> AnalysisResult:
        """执行解决方案分析。

        Execute solution analysis.

        Args:
            aggregation: 带宽聚合。/ Bandwidth aggregation.
            edge_allocations: 边到分配带宽的映射。
                / Edge-to-allocated-bandwidth mapping.
            service_allocations: 服务到分配带宽的映射。
                / Service-to-allocated-bandwidth mapping.
            node_throughputs: 节点到通过带宽的映射。
                / Node-to-throughput mapping.

        Returns:
            分析结果。/ Analysis result.
        """
        service_demands = {s.service_id: s.demand for s in aggregation.services}
        edge_capacities = {e.edge_id: e.capacity for e in aggregation.edges}
        edge_costs = {e.edge_id: e.cost_per_unit for e in aggregation.edges}
        transfer_nodes = {
            n.node_id: n.max_bandwidth for n in aggregation.nodes if n.is_transfer
        }

        demand_violations = self.demand_constraint.check_demands(
            service_demands=service_demands,
            service_allocations=service_allocations,
        )

        edge_violations = self.edge_bw_constraint.check_edges(
            edge_capacities=edge_capacities,
            edge_allocations=edge_allocations,
        )

        service_max_caps = {s.service_id: s.demand * 2.0 for s in aggregation.services}
        service_violations = self.svc_cap_constraint.check_services(
            service_max_capacities=service_max_caps,
            service_allocations=service_allocations,
        )

        transfer_violations = self.transfer_node_constraint.check_nodes(
            transfer_nodes=transfer_nodes,
            node_throughputs=node_throughputs,
        )

        violation_summary = ViolationSummary(
            demand_violations=demand_violations,
            edge_violations=edge_violations,
            service_violations=service_violations,
            transfer_node_violations=transfer_violations,
        )

        total_cost = self.cost_objective.calculate_total_cost(
            edge_allocations, edge_costs
        )

        total_demand = sum(service_demands.values())
        met_demand = sum(
            min(service_allocations.get(sid, 0.0), demand)
            for sid, demand in service_demands.items()
        )
        demand_satisfaction = met_demand / total_demand if total_demand > 0.0 else 1.0

        total_capacity = sum(edge_capacities.values())
        total_allocated = sum(edge_allocations.values())
        capacity_utilization = (
            total_allocated / total_capacity if total_capacity > 0.0 else 0.0
        )

        feasibility_score = 1.0 if violation_summary.is_feasible else 0.0

        quality_metrics = QualityMetrics(
            total_cost=total_cost,
            capacity_utilization=capacity_utilization,
            demand_satisfaction=demand_satisfaction,
            feasibility_score=feasibility_score,
        )

        return AnalysisResult(
            violation_summary=violation_summary,
            quality_metrics=quality_metrics,
        )

    def quick_feasibility_check(
        self,
        *,
        aggregation: BandwidthAggregation,
        edge_allocations: dict[str, float],
        service_allocations: dict[str, float],
    ) -> bool:
        """快速可行性检查。

        Quick feasibility check.

        Args:
            aggregation: 带宽聚合。/ Bandwidth aggregation.
            edge_allocations: 边到分配带宽的映射。
                / Edge-to-allocated-bandwidth mapping.
            service_allocations: 服务到分配带宽的映射。
                / Service-to-allocated-bandwidth mapping.

        Returns:
            所有约束均满足时返回 True。
            True if all constraints are satisfied.
        """
        service_demands = {s.service_id: s.demand for s in aggregation.services}
        edge_capacities = {e.edge_id: e.capacity for e in aggregation.edges}

        if not self.demand_constraint.is_feasible(
            service_demands=service_demands,
            service_allocations=service_allocations,
        ):
            return False

        return self.edge_bw_constraint.is_feasible(
            edge_capacities=edge_capacities,
            edge_allocations=edge_allocations,
        )
