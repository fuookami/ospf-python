"""容量调度上下文 / Capacity scheduling context.

容量调度域的建模入口，负责初始化聚合并注册到优化模型。
The modeling entry point for the capacity scheduling domain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity_scheduling_aggregation import (
    CapacitySchedulingAggregation,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity_scheduling_model import (
    CapacitySchedulingModel,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.service.limits.capacity_capacity_constraint import (
    CapacityCapacityConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.service.limits.capacity_demand_constraint import (
    CapacityDemandConstraint,
)

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.assignment import (
        CapacityAssignment,
    )
    from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity import (
        SlotCapacity,
    )
    from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity_scheduling_modeling_config import (
        CapacitySchedulingModelingConfig,
    )
    from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.load import (
        SlotLoad,
    )


@dataclass(frozen=True)
class CapacitySchedulingContext:
    """容量调度上下文 / Capacity scheduling context.

    作为容量调度域对应用层暴露的建模入口，管理聚合状态
    和优化模型。

    Attributes:
        aggregation: 容量调度聚合 / Capacity scheduling aggregation.
        model: 优化模型 / Optimization model.
    """

    aggregation: CapacitySchedulingAggregation = field(
        default_factory=CapacitySchedulingAggregation,
    )
    model: CapacitySchedulingModel = field(
        default_factory=CapacitySchedulingModel,
    )

    def register_assignment(
        self,
        assignment: CapacityAssignment,
    ) -> CapacitySchedulingContext:
        """注册分配决策。"""
        return CapacitySchedulingContext(
            aggregation=self.aggregation.with_assignment(
                assignment,
            ),
            model=self.model,
        )

    def register_capacity(
        self,
        capacity: SlotCapacity,
    ) -> CapacitySchedulingContext:
        """注册容量记录。"""
        return CapacitySchedulingContext(
            aggregation=self.aggregation.with_capacity(
                capacity,
            ),
            model=self.model,
        )

    def register_load(
        self,
        load: SlotLoad,
    ) -> CapacitySchedulingContext:
        """注册负载记录。"""
        return CapacitySchedulingContext(
            aggregation=self.aggregation.with_load(load),
            model=self.model,
        )

    def get_capacity(
        self,
        capacity_slot_key: str,
    ) -> SlotCapacity | None:
        """获取指定容量槽的容量。"""
        return self.aggregation.get_capacity(capacity_slot_key)

    def remaining_capacity(
        self,
        capacity_slot_key: str,
    ) -> float:
        """获取指定容量槽的剩余容量。"""
        cap = self.aggregation.get_capacity(capacity_slot_key)
        if cap is None:
            return 0.0
        return cap.remaining_capacity

    def build_capacity_constraints(
        self,
    ) -> tuple[SlotCapacity, ...]:
        """构建容量约束。"""
        constraint = CapacityCapacityConstraint()
        return constraint.build_constraints(self.aggregation)

    def check_demand_feasibility(self) -> bool:
        """检查需求可行性。"""
        constraint = CapacityDemandConstraint()
        return constraint.is_feasible(self.aggregation)

    def with_config(
        self,
        config: CapacitySchedulingModelingConfig,
    ) -> CapacitySchedulingContext:
        """创建不同配置的上下文副本。"""
        return CapacitySchedulingContext(
            aggregation=self.aggregation,
            model=self.model.with_config(config),
        )
