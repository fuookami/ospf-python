"""任务编组排序约束 / Task compilation order constraint.

确保任务之间的排序关系得到满足。
Ensures that ordering relationships between tasks
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
class TaskOrderPair:
    """任务排序对 / Task order pair.

    Attributes:
        predecessor_key: 前序任务标识 / Predecessor task id.
        successor_key: 后序任务标识 / Successor task id.
        is_satisfied: 排序是否满足 / Whether order is satisfied.
        predecessor_end: 前序结束时间 / Predecessor end time.
        successor_start: 后序开始时间 / Successor start time.
    """

    predecessor_key: str
    successor_key: str
    is_satisfied: bool
    predecessor_end: float = 0.0
    successor_start: float = 0.0


@dataclass(frozen=True)
class TaskCompilationOrderConstraint:
    """任务编组排序约束 / Task compilation order constraint.

    生成任务编组排序约束数据，确保有依赖关系的任务按照规定
    的先后顺序执行。适用于需要保证前序任务完成后才能开始
    后续任务的场景。
    Generates task compilation order constraint data, ensuring
    tasks with dependencies execute in the specified sequence.
    Applicable when predecessor tasks must finish before
    successor tasks can begin.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "task_compilation_order"

    def build_constraints(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[TaskOrderPair, ...]:
        """构建任务排序约束列表。

        Build the list of task order constraints.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            排序约束数据元组。/ Tuple of order constraint data.
        """
        constraints: list[TaskOrderPair] = []
        for order in adapter.order_pairs:
            pred_end = adapter.task_end_time(
                order.predecessor_key,
            )
            succ_start = adapter.task_start_time(
                order.successor_key,
            )
            is_ok = pred_end <= succ_start + 1e-9
            constraints.append(
                TaskOrderPair(
                    predecessor_key=order.predecessor_key,
                    successor_key=order.successor_key,
                    is_satisfied=is_ok,
                    predecessor_end=pred_end,
                    successor_start=succ_start,
                )
            )
        return tuple(constraints)

    def constraint_name(
        self,
        *,
        predecessor_key: str,
        successor_key: str,
    ) -> str:
        """生成约束名称。"""
        return f"{self.constraint_name_prefix}_{predecessor_key}_{successor_key}"

    def is_satisfied(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> bool:
        """检查所有排序约束是否满足。"""
        return all(pair.is_satisfied for pair in self.build_constraints(adapter))

    def violations(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[TaskOrderPair, ...]:
        """获取所有违反排序约束的记录。"""
        return tuple(
            pair for pair in self.build_constraints(adapter) if not pair.is_satisfied
        )
