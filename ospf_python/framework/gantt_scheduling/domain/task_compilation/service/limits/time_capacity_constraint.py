"""时间容量约束 / Time capacity constraint.

确保每个时间窗口内的总任务使用量不超过该时段的容量上限。
Ensures that total task usage within each time window does
not exceed the capacity upper bound for that period.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_solver_value_adapter import (
        TaskCompilationSolverValueAdapter,
    )


@dataclass(frozen=True)
class TimeCapacityData:
    """时间容量约束数据 / Time capacity constraint data.

    Attributes:
        time_window_start: 时间窗口起始 / Time window start.
        time_window_end: 时间窗口结束 / Time window end.
        max_capacity: 最大容量 / Maximum capacity.
        used_capacity: 已使用容量 / Used capacity.
    """

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
class TimeCapacityConstraint:
    """时间容量约束 / Time capacity constraint.

    生成时间容量约束数据，用于注册到优化模型中。每条约束
    确保在指定时间窗口内，所有活跃任务的总量不超过该时段
    的容量上限。
    Generates time capacity constraint data for registration
    into the optimization model. Each constraint ensures that
    within a given time window, the total of all active tasks
    does not exceed the capacity upper bound for that period.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "time_capacity"

    def build_constraints(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[TimeCapacityData, ...]:
        """构建时间容量约束列表。

        Build the list of time capacity constraints.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            容量约束数据元组。/ Tuple of capacity constraint data.
        """
        constraints: list[TimeCapacityData] = []
        for tw in adapter.time_windows:
            active = adapter.tasks_active_in_window(
                tw.start,
                tw.end,
            )
            total = sum(a.demand_amount for a in active)
            constraints.append(
                TimeCapacityData(
                    time_window_start=tw.start,
                    time_window_end=tw.end,
                    max_capacity=tw.max_capacity,
                    used_capacity=total,
                )
            )
        return tuple(constraints)

    def constraint_name(
        self,
        *,
        window_start: float,
        window_end: float,
    ) -> str:
        """生成约束名称。

        Generate the constraint name.

        Args:
            window_start: 窗口起始。/ Window start.
            window_end: 窗口结束。/ Window end.

        Returns:
            约束名称字符串。/ Constraint name string.
        """
        return f"{self.constraint_name_prefix}_{window_start}_{window_end}"

    def is_satisfied(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> bool:
        """检查时间容量约束是否满足。

        Check whether time capacity constraints are satisfied.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            若所有约束均可满足则返回 True。
            True if all constraints can be satisfied.
        """
        return all(not cap.is_over_capacity for cap in self.build_constraints(adapter))

    def violations(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[TimeCapacityData, ...]:
        """获取所有违反时间容量约束的记录。

        Get all records that violate time capacity constraints.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            违反约束的数据元组。
            Tuple of data violating constraints.
        """
        return tuple(
            cap for cap in self.build_constraints(adapter) if cap.is_over_capacity
        )
