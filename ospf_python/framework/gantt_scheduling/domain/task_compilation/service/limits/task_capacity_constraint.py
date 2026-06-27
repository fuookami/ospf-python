"""任务容量约束 / Task capacity constraint.

确保每个任务在执行期间的资源使用量不超过任务容量上限。
Ensures that each task's resource usage during execution
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
class TaskCapacityData:
    """任务容量约束数据 / Task capacity constraint data.

    Attributes:
        task_key: 任务标识 / Task identifier.
        resource_key: 资源标识 / Resource identifier.
        max_capacity: 最大容量 / Maximum capacity.
        used_capacity: 已使用容量 / Used capacity.
    """

    task_key: str
    resource_key: str
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
class TaskCapacityConstraint:
    """任务容量约束 / Task capacity constraint.

    生成任务容量约束数据，用于注册到优化模型中。每条约束
    确保单个任务对资源的需求量不超过其容量限制。
    Generates task capacity constraint data for registration
    into the optimization model. Each constraint ensures that
    a task's demand on a resource does not exceed its capacity
    limit.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "task_capacity"

    def build_constraints(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[TaskCapacityData, ...]:
        """构建任务容量约束列表。

        Build the list of task capacity constraints.

        遍历所有任务和资源需求，校验每个任务对资源的需求量
        是否在容量范围内。
        Iterates over all tasks and resource demands, verifying
        that each task's demand on a resource is within capacity
        bounds.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            容量约束数据元组。/ Tuple of capacity constraint data.
        """
        constraints: list[TaskCapacityData] = []
        for task in adapter.tasks:
            for res_key, demand in task.resource_requirements:
                max_cap = adapter.resource_capacity(res_key)
                constraints.append(
                    TaskCapacityData(
                        task_key=task.task_key,
                        resource_key=res_key,
                        max_capacity=max_cap,
                        used_capacity=demand,
                    )
                )
        return tuple(constraints)

    def constraint_name(
        self,
        *,
        task_key: str,
        resource_key: str,
    ) -> str:
        """生成约束名称。

        Generate the constraint name.

        Args:
            task_key: 任务标识。/ Task identifier.
            resource_key: 资源标识。/ Resource identifier.

        Returns:
            约束名称字符串。/ Constraint name string.
        """
        return f"{self.constraint_name_prefix}_{task_key}_{resource_key}"

    def is_satisfied(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> bool:
        """检查任务容量约束是否满足。

        Check whether task capacity constraints are satisfied.

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
    ) -> tuple[TaskCapacityData, ...]:
        """获取所有违反约束的记录。

        Get all records that violate constraints.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            违反约束的数据元组。
            Tuple of data violating constraints.
        """
        return tuple(
            cap for cap in self.build_constraints(adapter) if cap.is_over_capacity
        )
