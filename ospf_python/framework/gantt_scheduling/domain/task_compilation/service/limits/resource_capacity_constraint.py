"""资源容量约束 / Resource capacity constraint.

确保每个资源在任意时间窗口内的使用量不超过其容量上限。
Ensures that each resource's usage within any time window
does not exceed its capacity upper bound.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_solver_value_adapter import (
        TaskCompilationSolverValueAdapter,
    )


@dataclass(frozen=True)
class ResourceCapacityData:
    """资源容量约束数据 / Resource capacity constraint data.

    Attributes:
        resource_key: 资源标识 / Resource identifier.
        time_window_start: 时间窗口起始 / Time window start.
        time_window_end: 时间窗口结束 / Time window end.
        max_capacity: 最大容量 / Maximum capacity.
        used_capacity: 已使用容量 / Used capacity.
    """

    resource_key: str
    time_window_start: float
    time_window_end: float
    max_capacity: float
    used_capacity: float = 0.0

    @property
    def remaining_capacity(self) -> float:
        """剩余容量 / Remaining capacity."""
        return max(0.0, self.max_capacity - self.used_capacity)

    @property
    def utilization_ratio(self) -> float:
        """利用率 / Utilization ratio."""
        if self.max_capacity <= 0.0:
            return 0.0
        return min(1.0, self.used_capacity / self.max_capacity)

    @property
    def is_over_capacity(self) -> bool:
        """是否超容 / Whether over capacity."""
        return self.used_capacity > self.max_capacity


@dataclass(frozen=True)
class ResourceCapacityConstraint:
    """资源容量约束 / Resource capacity constraint.

    生成资源容量约束数据，用于注册到优化模型中。每条约束
    确保在指定时间窗口内，所有任务对资源的需求总量不超过
    资源容量上限。
    Generates resource capacity constraint data for registration
    into the optimization model. Each constraint ensures that
    within a given time window, the total demand from all tasks
    on a resource does not exceed the resource capacity upper
    bound.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "resource_capacity"

    def build_constraints(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[ResourceCapacityData, ...]:
        """构建资源容量约束列表。

        Build the list of resource capacity constraints.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            容量约束数据元组。/ Tuple of capacity constraint data.
        """
        constraints: list[ResourceCapacityData] = []
        for cap in adapter.resource_capacities:
            overlapping = adapter.demands_in_window(
                resource_key=cap.resource_key,
                window_start=cap.time_window_start,
                window_end=cap.time_window_end,
            )
            total = sum(d.demand_amount for d in overlapping)
            constraints.append(
                ResourceCapacityData(
                    resource_key=cap.resource_key,
                    time_window_start=cap.time_window_start,
                    time_window_end=cap.time_window_end,
                    max_capacity=cap.max_capacity,
                    used_capacity=total,
                )
            )
        return tuple(constraints)

    def constraint_name(
        self,
        *,
        resource_key: str,
        window_start: float,
        window_end: float,
    ) -> str:
        """生成约束名称。"""
        return (
            f"{self.constraint_name_prefix}_{resource_key}_{window_start}_{window_end}"
        )

    def is_satisfied(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> bool:
        """检查资源容量约束是否满足。"""
        return all(not cap.is_over_capacity for cap in self.build_constraints(adapter))

    def violations(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[ResourceCapacityData, ...]:
        """获取所有违反资源容量约束的记录。"""
        return tuple(
            cap for cap in self.build_constraints(adapter) if cap.is_over_capacity
        )
