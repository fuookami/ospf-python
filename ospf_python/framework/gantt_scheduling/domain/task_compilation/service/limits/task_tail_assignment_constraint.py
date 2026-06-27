"""任务尾部分配约束 / Task tail assignment constraint.

确保任务的尾部分配满足约束要求。
Ensures that task tail assignments satisfy constraint
requirements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_solver_value_adapter import (
        TaskCompilationSolverValueAdapter,
    )


@dataclass(frozen=True)
class TailAssignmentData:
    """尾部分配数据 / Tail assignment data.

    Attributes:
        task_key: 任务标识 / Task identifier.
        tail_resource_key: 尾部资源标识 / Tail resource id.
        is_assigned: 是否已分配 / Whether assigned.
        assigned_amount: 已分配量 / Assigned amount.
        required_amount: 需求量 / Required amount.
    """

    task_key: str
    tail_resource_key: str
    is_assigned: bool
    assigned_amount: float
    required_amount: float


@dataclass(frozen=True)
class TaskTailAssignmentConstraint:
    """任务尾部分配约束 / Task tail assignment constraint.

    生成任务尾部分配约束数据，确保每个任务的尾部资源
    分配满足要求。尾部分配通常指任务完成后对特定资源
    的后续使用安排。
    Generates task tail assignment constraint data, ensuring
    each task's tail resource assignment meets requirements.
    Tail assignment typically refers to the subsequent use of
    specific resources after task completion.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "tail_assignment"

    def build_constraints(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[TailAssignmentData, ...]:
        """构建尾部分配约束列表。

        Build the list of tail assignment constraints.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            尾部分配约束数据元组。
            Tuple of tail assignment constraint data.
        """
        constraints: list[TailAssignmentData] = []
        for task in adapter.tasks:
            tail_res = adapter.tail_resource(task.task_key)
            if tail_res is None:
                continue
            required = adapter.tail_required_amount(
                task.task_key,
            )
            assigned = adapter.tail_assigned_amount(
                task.task_key,
            )
            is_ok = assigned >= required - 1e-9
            constraints.append(
                TailAssignmentData(
                    task_key=task.task_key,
                    tail_resource_key=tail_res,
                    is_assigned=is_ok,
                    assigned_amount=assigned,
                    required_amount=required,
                )
            )
        return tuple(constraints)

    def constraint_name(self, task_key: str) -> str:
        """生成约束名称。"""
        return f"{self.constraint_name_prefix}_{task_key}"

    def is_satisfied(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> bool:
        """检查所有尾部分配约束是否满足。"""
        return all(data.is_assigned for data in self.build_constraints(adapter))

    def violations(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[TailAssignmentData, ...]:
        """获取所有违反尾部分配约束的记录。"""
        return tuple(
            data for data in self.build_constraints(adapter) if not data.is_assigned
        )
