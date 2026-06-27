"""前置约束 / Precedence constraint.

确保任务之间的前置依赖关系得到满足。
Ensures that precedence dependencies between tasks
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
class PrecedencePair:
    """前置依赖对 / Precedence pair.

    Attributes:
        predecessor_key: 前序任务标识 / Predecessor task id.
        successor_key: 后序任务标识 / Successor task id.
        min_lag: 最小间隔时间 / Minimum lag time.
        is_satisfied: 依赖是否满足 / Whether satisfied.
        actual_lag: 实际间隔时间 / Actual lag time.
    """

    predecessor_key: str
    successor_key: str
    min_lag: float
    is_satisfied: bool
    actual_lag: float = 0.0


@dataclass(frozen=True)
class PrecedenceConstraint:
    """前置约束 / Precedence constraint.

    生成前置约束数据，确保任务之间的时间间隔满足最小延迟
    要求。适用于需要保证前序任务完成后等待一定时间才能
    开始后续任务的场景。
    Generates precedence constraint data, ensuring time gaps
    between tasks meet minimum lag requirements. Applicable
    when a waiting period is required after a predecessor
    finishes before the successor can begin.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "precedence"

    def build_constraints(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[PrecedencePair, ...]:
        """构建前置约束列表。

        Build the list of precedence constraints.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            前置约束数据元组。/ Tuple of precedence constraint data.
        """
        constraints: list[PrecedencePair] = []
        for prec in adapter.precedence_pairs:
            pred_end = adapter.task_end_time(
                prec.predecessor_key,
            )
            succ_start = adapter.task_start_time(
                prec.successor_key,
            )
            actual_lag = succ_start - pred_end
            is_ok = actual_lag >= prec.min_lag - 1e-9
            constraints.append(
                PrecedencePair(
                    predecessor_key=prec.predecessor_key,
                    successor_key=prec.successor_key,
                    min_lag=prec.min_lag,
                    is_satisfied=is_ok,
                    actual_lag=actual_lag,
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
        """检查所有前置约束是否满足。"""
        return all(pair.is_satisfied for pair in self.build_constraints(adapter))

    def violations(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[PrecedencePair, ...]:
        """获取所有违反前置约束的记录。"""
        return tuple(
            pair for pair in self.build_constraints(adapter) if not pair.is_satisfied
        )
