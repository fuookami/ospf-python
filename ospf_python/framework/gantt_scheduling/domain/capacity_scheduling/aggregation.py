"""容量调度顶层聚合 / Capacity scheduling top-level aggregation.

组合容量调度域的顶层视图。
Combines the top-level view of the capacity scheduling domain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity_scheduling_model import (
    CapacitySchedulingModel,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.service.limits.capacity_capacity_constraint import (
    CapacityCapacityConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.service.limits.capacity_demand_constraint import (
    CapacityDemandConstraint,
    DemandSatisfaction,
)

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity import (
        SlotCapacity,
    )


@dataclass(frozen=True)
class Aggregation:
    """容量调度顶层聚合 / Capacity scheduling top-level aggregation.

    提供容量调度域的顶层视图，整合模型数据和约束检查。

    Attributes:
        model: 容量调度模型 / Capacity scheduling model.
    """

    model: CapacitySchedulingModel = field(
        default_factory=CapacitySchedulingModel,
    )

    def is_feasible(self) -> bool:
        """检查是否可行 / Check whether feasible."""
        cap_constraint = CapacityCapacityConstraint()
        demand_constraint = CapacityDemandConstraint()
        return cap_constraint.is_feasible(
            self.model.aggregation
        ) and demand_constraint.is_feasible(
            self.model.aggregation,
        )

    def capacity_violations(
        self,
    ) -> tuple[SlotCapacity, ...]:
        """获取容量违反 / Get capacity violations."""
        constraint = CapacityCapacityConstraint()
        return constraint.violations(self.model.aggregation)

    def demand_violations(self) -> tuple[DemandSatisfaction, ...]:
        """获取需求违反 / Get demand violations."""
        constraint = CapacityDemandConstraint()
        return constraint.unsatisfied_demands(
            self.model.aggregation,
        )

    def with_model(
        self,
        model: CapacitySchedulingModel,
    ) -> Aggregation:
        """创建不同模型的聚合副本。"""
        return Aggregation(model=model)
