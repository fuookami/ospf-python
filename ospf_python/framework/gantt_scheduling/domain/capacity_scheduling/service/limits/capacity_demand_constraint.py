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
        """构建需求约束列表。

        Build the demand satisfaction list.

        一次遍历把每个工作项的分配量累加好，而不是对每个工作项再调用一次
        `assignments_for_work_item`（那是 O(项 × 分配)，本方法在 500 项时原来要 18 ms）。
        累加顺序与逐项 `sum(...)` 相同（都按分配注册的顺序）。
        **输出顺序仍取 `work_item_keys`**，与改前逐字一致。
        One pass accumulates each work item's assigned amount instead of calling
        `assignments_for_work_item` per item (O(items x assignments); 18 ms at 500 items).
        The summation order matches the per-item `sum(...)`, and the emitted order still
        comes from `work_item_keys`, exactly as before.
        """
        totals: dict[str, float] = {}
        for assignment in aggregation.assignments:
            key = getattr(assignment, "work_item_key", "")
            totals[key] = totals.get(key, 0.0) + getattr(
                assignment, "assignment_amount", 0.0
            )

        results: list[DemandSatisfaction] = []
        for work_item_key in aggregation.work_item_keys:
            total_assigned = totals.get(work_item_key, 0.0)
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
