"""序列相关换产约束 / Sequence dependent setup constraint.

确保相邻任务之间的换产时间满足序列相关换产矩阵的要求。
Ensures that setup times between adjacent tasks satisfy
the sequence-dependent setup time matrix requirements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_solver_value_adapter import (
        TaskCompilationSolverValueAdapter,
    )


@dataclass(frozen=True)
class SetupTimeData:
    """换产时间数据 / Setup time data.

    Attributes:
        predecessor_key: 前序任务标识 / Predecessor task id.
        successor_key: 后序任务标识 / Successor task id.
        required_setup: 要求的换产时间 / Required setup time.
        actual_gap: 实际间隔时间 / Actual gap time.
        is_satisfied: 是否满足 / Whether satisfied.
    """

    predecessor_key: str
    successor_key: str
    required_setup: float
    actual_gap: float
    is_satisfied: bool


@dataclass(frozen=True)
class SequenceDependentSetupConstraint:
    """序列相关换产约束 / Sequence dependent setup constraint.

    生成序列相关换产约束数据，确保相邻任务之间的间隔时间
    不少于换产矩阵中规定的最小换产时间。换产时间取决于
    前序任务和后序任务的组合。
    Generates sequence-dependent setup constraint data,
    ensuring the gap between adjacent tasks is no less than
    the minimum setup time from the setup matrix. The setup
    time depends on the combination of predecessor and
    successor tasks.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "seq_setup"

    def build_constraints(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[SetupTimeData, ...]:
        """构建换产约束列表。

        Build the list of setup constraints.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            换产约束数据元组。/ Tuple of setup constraint data.
        """
        constraints: list[SetupTimeData] = []
        for pair in adapter.adjacent_task_pairs:
            setup_time = adapter.setup_time_between(
                pair.predecessor_key,
                pair.successor_key,
            )
            pred_end = adapter.task_end_time(
                pair.predecessor_key,
            )
            succ_start = adapter.task_start_time(
                pair.successor_key,
            )
            actual_gap = succ_start - pred_end
            is_ok = actual_gap >= setup_time - 1e-9
            constraints.append(
                SetupTimeData(
                    predecessor_key=pair.predecessor_key,
                    successor_key=pair.successor_key,
                    required_setup=setup_time,
                    actual_gap=actual_gap,
                    is_satisfied=is_ok,
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
        """检查所有换产约束是否满足。"""
        return all(data.is_satisfied for data in self.build_constraints(adapter))

    def violations(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[SetupTimeData, ...]:
        """获取所有违反换产约束的记录。"""
        return tuple(
            data for data in self.build_constraints(adapter) if not data.is_satisfied
        )
