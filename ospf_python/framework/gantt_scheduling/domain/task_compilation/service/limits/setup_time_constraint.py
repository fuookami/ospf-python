"""换产时间约束 / Setup time constraint.

确保任务之间的换产时间得到正确安排。
Ensures that setup times between tasks are properly
scheduled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_solver_value_adapter import (
        TaskCompilationSolverValueAdapter,
    )


@dataclass(frozen=True)
class SetupTimePair:
    """换产时间对 / Setup time pair.

    Attributes:
        task_key: 任务标识 / Task identifier.
        setup_duration: 换产时长 / Setup duration.
        start_time: 换产开始时间 / Setup start time.
        end_time: 换产结束时间 / Setup end time.
        is_satisfied: 是否满足 / Whether satisfied.
    """

    task_key: str
    setup_duration: float
    start_time: float
    end_time: float
    is_satisfied: bool


@dataclass(frozen=True)
class SetupTimeConstraint:
    """换产时间约束 / Setup time constraint.

    生成换产时间约束数据，确保每个任务的换产时间在调度中
    得到正确考虑。适用于需要在任务执行前安排固定换产时间
    的场景。
    Generates setup time constraint data, ensuring each task's
    setup time is correctly considered in the schedule.
    Applicable when a fixed setup time must be scheduled
    before task execution.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "setup_time"

    def build_constraints(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[SetupTimePair, ...]:
        """构建换产时间约束列表。

        Build the list of setup time constraints.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            换产时间约束数据元组。
            Tuple of setup time constraint data.
        """
        constraints: list[SetupTimePair] = []
        for task in adapter.tasks:
            setup = adapter.setup_duration(task.task_key)
            if setup <= 0.0:
                continue
            task_start = adapter.task_start_time(
                task.task_key,
            )
            setup_end = task_start
            setup_start = setup_end - setup
            is_ok = setup_start >= adapter.earliest_available(
                task.task_key,
            )
            constraints.append(
                SetupTimePair(
                    task_key=task.task_key,
                    setup_duration=setup,
                    start_time=setup_start,
                    end_time=setup_end,
                    is_satisfied=is_ok,
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
        """检查所有换产时间约束是否满足。"""
        return all(pair.is_satisfied for pair in self.build_constraints(adapter))

    def violations(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[SetupTimePair, ...]:
        """获取所有违反换产时间约束的记录。"""
        return tuple(
            pair for pair in self.build_constraints(adapter) if not pair.is_satisfied
        )
