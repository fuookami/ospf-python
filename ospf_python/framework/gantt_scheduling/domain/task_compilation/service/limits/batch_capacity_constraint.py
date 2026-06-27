"""批次容量约束 / Batch capacity constraint.

确保每个批次在任意时间窗口内的使用量不超过其容量上限。
Ensures that each batch's usage within any time window does
not exceed its capacity upper bound.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_solver_value_adapter import (
        TaskCompilationSolverValueAdapter,
    )


@dataclass(frozen=True)
class BatchCapacityData:
    """批次容量约束数据 / Batch capacity constraint data.

    Attributes:
        batch_key: 批次标识 / Batch identifier.
        time_window_start: 时间窗口起始 / Time window start.
        time_window_end: 时间窗口结束 / Time window end.
        max_capacity: 最大容量 / Maximum capacity.
        used_capacity: 已使用容量 / Used capacity.
    """

    batch_key: str
    time_window_start: float
    time_window_end: float
    max_capacity: float
    used_capacity: float = 0.0

    @property
    def remaining_capacity(self) -> float:
        """剩余容量 / Remaining capacity."""
        return max(0.0, self.max_capacity - self.used_capacity)

    @property
    def is_over_capacity(self) -> bool:
        """是否超容 / Whether over capacity."""
        return self.used_capacity > self.max_capacity


@dataclass(frozen=True)
class BatchCapacityConstraint:
    """批次容量约束 / Batch capacity constraint.

    生成批次容量约束数据，用于注册到优化模型中。每条约束
    确保在指定时间窗口内，所有任务对批次的需求总量不超过
    批次容量上限。
    Generates batch capacity constraint data for registration
    into the optimization model. Each constraint ensures that
    within a given time window, the total demand from all tasks
    on a batch does not exceed the batch capacity upper bound.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "batch_capacity"

    def build_constraints(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[BatchCapacityData, ...]:
        """构建批次容量约束列表。

        Build the list of batch capacity constraints.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            容量约束数据元组。/ Tuple of capacity constraint data.
        """
        constraints: list[BatchCapacityData] = []
        for cap in adapter.batch_capacities:
            total = adapter.total_load_for_batch(
                cap.batch_key,
            )
            constraints.append(
                BatchCapacityData(
                    batch_key=cap.batch_key,
                    time_window_start=cap.time_window_start,
                    time_window_end=cap.time_window_end,
                    max_capacity=cap.max_capacity,
                    used_capacity=total,
                )
            )
        return tuple(constraints)

    def constraint_name(self, batch_key: str) -> str:
        """生成约束名称。"""
        return f"{self.constraint_name_prefix}_{batch_key}"

    def is_satisfied(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> bool:
        """检查批次容量约束是否满足。"""
        return all(not cap.is_over_capacity for cap in self.build_constraints(adapter))

    def violations(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[BatchCapacityData, ...]:
        """获取所有违反批次容量约束的记录。"""
        return tuple(
            cap for cap in self.build_constraints(adapter) if cap.is_over_capacity
        )
