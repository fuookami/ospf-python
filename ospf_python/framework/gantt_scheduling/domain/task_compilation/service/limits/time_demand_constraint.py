"""时间需求约束 / Time demand constraint.

确保每个时间窗口内的任务需求得到满足。
Ensures that task demands within each time window
are satisfied.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_solver_value_adapter import (
        TaskCompilationSolverValueAdapter,
    )


@dataclass(frozen=True)
class TimeDemandSatisfaction:
    """时间需求满足状态 / Time demand satisfaction status.

    Attributes:
        time_window_start: 时间窗口起始 / Time window start.
        time_window_end: 时间窗口结束 / Time window end.
        is_satisfied: 是否已满足 / Whether satisfied.
        required_amount: 需求量 / Required amount.
        assigned_amount: 已分配量 / Assigned amount.
        shortfall: 缺口量 / Shortfall amount.
    """

    time_window_start: float
    time_window_end: float
    is_satisfied: bool
    required_amount: float
    assigned_amount: float
    shortfall: float


@dataclass(frozen=True)
class TimeDemandConstraint:
    """时间需求约束 / Time demand constraint.

    生成时间需求约束数据，确保每个时间窗口内的任务需求
    在可用产能范围内得到满足。
    Generates time demand constraint data, ensuring task
    demands within each time window are satisfied within
    available capacity.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "time_demand"

    def build_constraints(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[TimeDemandSatisfaction, ...]:
        """构建时间需求约束列表。

        Build the list of time demand constraints.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            时间需求满足状态元组。
            Tuple of time demand satisfaction data.
        """
        results: list[TimeDemandSatisfaction] = []
        for tw in adapter.time_windows:
            required = adapter.demand_required_in_window(
                tw.start,
                tw.end,
            )
            assigned = adapter.demand_assigned_in_window(
                tw.start,
                tw.end,
            )
            shortfall = max(0.0, required - assigned)
            results.append(
                TimeDemandSatisfaction(
                    time_window_start=tw.start,
                    time_window_end=tw.end,
                    is_satisfied=shortfall <= 1e-9,
                    required_amount=required,
                    assigned_amount=assigned,
                    shortfall=shortfall,
                )
            )
        return tuple(results)

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

    def unsatisfied_demands(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[TimeDemandSatisfaction, ...]:
        """获取所有未满足的时间需求。

        Get all unsatisfied time demands.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            未满足的需求元组。/ Tuple of unsatisfied demands.
        """
        return tuple(s for s in self.build_constraints(adapter) if not s.is_satisfied)

    def is_satisfied(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> bool:
        """检查所有时间需求是否满足。

        Check whether all time demands are satisfied.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            若所有需求均可满足则返回 True。
            True if all demands can be satisfied.
        """
        return len(self.unsatisfied_demands(adapter)) == 0

    def violations(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[TimeDemandSatisfaction, ...]:
        """获取违反约束的记录。

        Get records that violate constraints.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            违反约束的需求记录元组。
            Tuple of demand records violating constraints.
        """
        return self.unsatisfied_demands(adapter)
