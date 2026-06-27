"""时间排序约束 / Time order constraint.

确保时间窗口之间的排序关系得到满足。
Ensures that ordering relationships between time windows
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
class TimeOrderPair:
    """时间排序对 / Time order pair.

    Attributes:
        predecessor_window_start: 前序窗口起始 /
            Predecessor window start.
        predecessor_window_end: 前序窗口结束 /
            Predecessor window end.
        successor_window_start: 后序窗口起始 /
            Successor window start.
        successor_window_end: 后序窗口结束 /
            Successor window end.
        is_satisfied: 排序是否满足 / Whether order satisfied.
    """

    predecessor_window_start: float
    predecessor_window_end: float
    successor_window_start: float
    successor_window_end: float
    is_satisfied: bool


@dataclass(frozen=True)
class TimeOrderConstraint:
    """时间排序约束 / Time order constraint.

    生成时间排序约束数据，确保时间窗口按照规定的先后顺序
    排列。适用于需要保证前序时间窗口完全结束后才能开始
    后续时间窗口的场景。
    Generates time order constraint data, ensuring time windows
    are arranged in the specified sequence. Applicable when
    a predecessor window must fully end before the successor
    window can begin.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "time_order"

    def build_constraints(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[TimeOrderPair, ...]:
        """构建时间排序约束列表。

        Build the list of time order constraints.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            排序约束数据元组。/ Tuple of order constraint data.
        """
        constraints: list[TimeOrderPair] = []
        windows = adapter.time_windows
        for i in range(len(windows) - 1):
            curr = windows[i]
            nxt = windows[i + 1]
            is_ok = curr.end <= nxt.start + 1e-9
            constraints.append(
                TimeOrderPair(
                    predecessor_window_start=curr.start,
                    predecessor_window_end=curr.end,
                    successor_window_start=nxt.start,
                    successor_window_end=nxt.end,
                    is_satisfied=is_ok,
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
        """检查所有时间排序约束是否满足。

        Check whether all time order constraints are satisfied.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            若所有排序约束均可满足则返回 True。
            True if all order constraints can be satisfied.
        """
        return all(pair.is_satisfied for pair in self.build_constraints(adapter))

    def violations(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[TimeOrderPair, ...]:
        """获取所有违反时间排序约束的记录。

        Get all records that violate time order constraints.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            违反约束的排序对元组。
            Tuple of order pairs violating constraints.
        """
        return tuple(
            pair for pair in self.build_constraints(adapter) if not pair.is_satisfied
        )
