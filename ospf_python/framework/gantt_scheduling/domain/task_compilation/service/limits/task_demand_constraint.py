"""任务需求约束 / Task demand constraint.

确保每个任务的资源需求得到满足。
Ensures that each task's resource demand is satisfied.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_solver_value_adapter import (
        TaskCompilationSolverValueAdapter,
    )


@dataclass(frozen=True)
class TaskDemandSatisfaction:
    """任务需求满足状态 / Task demand satisfaction status.

    Attributes:
        task_key: 任务标识 / Task identifier.
        resource_key: 资源标识 / Resource identifier.
        is_satisfied: 是否已满足 / Whether satisfied.
        required_amount: 需求量 / Required amount.
        assigned_amount: 已分配量 / Assigned amount.
        shortfall: 缺口量 / Shortfall amount.
    """

    task_key: str
    resource_key: str
    is_satisfied: bool
    required_amount: float
    assigned_amount: float
    shortfall: float


@dataclass(frozen=True)
class TaskDemandConstraint:
    """任务需求约束 / Task demand constraint.

    生成任务需求约束数据，确保每个任务在所有相关资源上的
    需求得到满足。支持刚性需求和柔性需求。
    Generates task demand constraint data, ensuring each task's
    demand on all relevant resources is satisfied. Supports
    mandatory and flexible demands.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "task_demand"

    def build_constraints(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[TaskDemandSatisfaction, ...]:
        """构建任务需求约束列表。

        Build the list of task demand constraints.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            需求满足状态元组。/ Tuple of demand satisfaction data.
        """
        results: list[TaskDemandSatisfaction] = []
        for task in adapter.tasks:
            for res_key, amount in task.resource_requirements:
                assigned = adapter.assigned_amount(
                    task.task_key,
                    res_key,
                )
                shortfall = max(0.0, amount - assigned)
                results.append(
                    TaskDemandSatisfaction(
                        task_key=task.task_key,
                        resource_key=res_key,
                        is_satisfied=shortfall <= 1e-9,
                        required_amount=amount,
                        assigned_amount=assigned,
                        shortfall=shortfall,
                    )
                )
        return tuple(results)

    def constraint_name(
        self,
        *,
        task_key: str,
        resource_key: str,
    ) -> str:
        """生成约束名称。"""
        return f"{self.constraint_name_prefix}_{task_key}_{resource_key}"

    def unsatisfied_demands(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[TaskDemandSatisfaction, ...]:
        """获取所有未满足的需求。"""
        return tuple(s for s in self.build_constraints(adapter) if not s.is_satisfied)

    def is_satisfied(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> bool:
        """检查所有需求是否满足。"""
        return len(self.unsatisfied_demands(adapter)) == 0

    def violations(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[TaskDemandSatisfaction, ...]:
        """获取违反约束的记录。"""
        return self.unsatisfied_demands(adapter)
