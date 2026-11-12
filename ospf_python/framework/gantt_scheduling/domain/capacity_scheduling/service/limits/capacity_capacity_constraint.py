"""容量调度容量约束 / Capacity scheduling capacity constraint.

确保每个容量槽在任意时间窗口内的使用量不超过其容量上限。
Ensures that each capacity slot's usage within any time window
does not exceed its capacity upper bound.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity import (
    SlotCapacity,
)

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity_scheduling_aggregation import (
        CapacitySchedulingAggregation,
    )


@dataclass(frozen=True)
class CapacityCapacityConstraint:
    """容量调度容量约束 / Capacity scheduling capacity constraint.

    生成容量槽容量约束数据，用于注册到优化模型中。每条约束
    确保在指定时间窗口内，所有工作项对容量槽的需求总量不
    超过容量上限。

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "cap_capacity"

    def build_constraints(
        self,
        aggregation: CapacitySchedulingAggregation,
    ) -> tuple[SlotCapacity, ...]:
        """构建容量约束列表。

        Build the list of capacity constraints.

        Args:
            aggregation: 容量调度聚合。/ Capacity scheduling aggregation.

        Returns:
            容量约束数据元组。/ Tuple of capacity constraint data.

        一次遍历把负载按槽累加好，而不是对每个容量记录再调用一次
        `total_load_for_slot`（那是 O(容量 × 负载)）。累加顺序与逐槽 `sum(...)` 相同，
        浮点结果一致。

        **聚合类没有公开 `loads` 元组时退回逐槽访问器**——替身（例如
        `test_capacity_scheduling.py` 的 `_StubAggregation`，其负载存成「槽 → 负载」的
        dict）只实现 `total_load_for_slot`。两条路语义相同，只是复杂度不同。

        Accumulate load per slot once instead of calling `total_load_for_slot` per
        capacity record (O(capacities x loads)); summation order unchanged. Falls back to
        the per-slot accessor when the aggregation does not expose a `loads` tuple.
        """
        loads_raw = getattr(aggregation, "loads", None)
        loads_by_slot: dict[str, float] = {}
        if loads_raw is not None:
            for load in loads_raw:
                key = getattr(load, "capacity_slot_key", None)
                if key is not None:
                    loads_by_slot[key] = loads_by_slot.get(key, 0.0) + getattr(
                        load, "load_amount", 0.0
                    )

        constraints: list[SlotCapacity] = []
        for cap in aggregation.capacities:
            total_demand = (
                loads_by_slot.get(cap.capacity_slot_key, 0.0)
                if loads_raw is not None
                else aggregation.total_load_for_slot(cap.capacity_slot_key)
            )
            constraints.append(
                SlotCapacity(
                    capacity_slot_key=cap.capacity_slot_key,
                    time_window_start=cap.time_window_start,
                    time_window_end=cap.time_window_end,
                    max_capacity=cap.max_capacity,
                    used_capacity=total_demand,
                )
            )
        return tuple(constraints)

    def constraint_name(
        self,
        slot_key: str,
    ) -> str:
        """生成约束名称。"""
        return f"{self.constraint_name_prefix}_{slot_key}"

    def is_feasible(
        self,
        aggregation: CapacitySchedulingAggregation,
    ) -> bool:
        """检查容量约束是否可行。"""
        for cap in self.build_constraints(aggregation):
            if cap.used_capacity > cap.max_capacity:
                return False
        return True

    def violations(
        self,
        aggregation: CapacitySchedulingAggregation,
    ) -> tuple[SlotCapacity, ...]:
        """获取所有违反容量约束的记录。"""
        return tuple(
            cap
            for cap in self.build_constraints(aggregation)
            if cap.used_capacity > cap.max_capacity
        )
