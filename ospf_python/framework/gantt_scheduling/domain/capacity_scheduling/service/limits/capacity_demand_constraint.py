"""容量调度需求约束 / Capacity scheduling demand constraint.

确保每个工作项的容量需求得到满足。
Ensures that each work item's capacity demand is satisfied.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity_scheduling_aggregation import (
        CapacitySchedulingAggregation,
    )


@dataclass(frozen=True)
class DemandSatisfaction:
    """需求满足状态 / Demand satisfaction status.

    Attributes:
        work_item_key: 工作项标识 / Work item identifier.
        is_satisfied: 是否已满足 / Whether satisfied.
        assigned_amount: 已分配量 / Assigned amount.
        shortfall: 缺口量 / Shortfall amount.
    """

    work_item_key: str
    is_satisfied: bool
    assigned_amount: float
    shortfall: float


@dataclass(frozen=True)
class CapacityDemandConstraint:
    """容量调度需求约束 / Capacity scheduling demand constraint.

    生成容量调度需求约束数据，确保每个工作项的容量需求
    在可用容量范围内得到满足。

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
        required_amount: 要求的分配量，0.0 表示使用实际需求 /
            Required amount, 0.0 means use actual demand.
    """

    constraint_name_prefix: str = "cap_demand"
    required_amount: float = 0.0

    def build_constraints(
        self,
        aggregation: CapacitySchedulingAggregation,
    ) -> tuple[DemandSatisfaction, ...]:
        """构建需求约束列表。"""
        results: list[DemandSatisfaction] = []
        for work_item_key in aggregation.work_item_keys:
            item_assignments = aggregation.assignments_for_work_item(
                work_item_key,
            )
            total_assigned = sum(a.assignment_amount for a in item_assignments)
            required = (
                self.required_amount if self.required_amount > 0.0 else total_assigned
            )
            shortfall = max(0.0, required - total_assigned)
            results.append(
                DemandSatisfaction(
                    work_item_key=work_item_key,
                    is_satisfied=shortfall <= 1e-9,
                    assigned_amount=total_assigned,
                    shortfall=shortfall,
                )
            )
        return tuple(results)

    def constraint_name(
        self,
        work_item_key: str,
    ) -> str:
        """生成约束名称。"""
        return f"{self.constraint_name_prefix}_{work_item_key}"

    def unsatisfied_demands(
        self,
        aggregation: CapacitySchedulingAggregation,
    ) -> tuple[DemandSatisfaction, ...]:
        """获取所有未满足的需求。"""
        return tuple(
            s for s in self.build_constraints(aggregation) if not s.is_satisfied
        )

    def is_feasible(
        self,
        aggregation: CapacitySchedulingAggregation,
    ) -> bool:
        """检查所有需求是否可行。"""
        return len(self.unsatisfied_demands(aggregation)) == 0
