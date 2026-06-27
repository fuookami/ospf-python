"""批次需求约束 / Batch demand constraint.

确保每个批次的需求得到满足。
Ensures that each batch's demand is satisfied.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_solver_value_adapter import (
        TaskCompilationSolverValueAdapter,
    )


@dataclass(frozen=True)
class BatchDemandSatisfaction:
    """批次需求满足状态 / Batch demand satisfaction status.

    Attributes:
        batch_key: 批次标识 / Batch identifier.
        is_satisfied: 是否已满足 / Whether satisfied.
        assigned_amount: 已分配量 / Assigned amount.
        shortfall: 缺口量 / Shortfall amount.
    """

    batch_key: str
    is_satisfied: bool
    assigned_amount: float
    shortfall: float


@dataclass(frozen=True)
class BatchDemandConstraint:
    """批次需求约束 / Batch demand constraint.

    生成批次需求约束数据，确保每个批次的任务需求
    在可用产能范围内得到满足。
    Generates batch demand constraint data, ensuring each
    batch's task demand is satisfied within available capacity.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
        required_amount: 要求的分配量，0.0 表示使用实际需求 /
            Required amount, 0.0 means use actual demand.
    """

    constraint_name_prefix: str = "batch_demand"
    required_amount: float = 0.0

    def build_constraints(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[BatchDemandSatisfaction, ...]:
        """构建批次需求约束列表。

        Build the list of batch demand constraints.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            批次需求满足状态元组。
            Tuple of batch demand satisfaction data.
        """
        results: list[BatchDemandSatisfaction] = []
        for batch_key in adapter.batch_keys:
            total = adapter.total_assigned_for_batch(batch_key)
            required = self.required_amount if self.required_amount > 0.0 else total
            shortfall = max(0.0, required - total)
            results.append(
                BatchDemandSatisfaction(
                    batch_key=batch_key,
                    is_satisfied=shortfall <= 1e-9,
                    assigned_amount=total,
                    shortfall=shortfall,
                )
            )
        return tuple(results)

    def constraint_name(self, batch_key: str) -> str:
        """生成约束名称。"""
        return f"{self.constraint_name_prefix}_{batch_key}"

    def unsatisfied_demands(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[BatchDemandSatisfaction, ...]:
        """获取所有未满足的批次需求。"""
        return tuple(s for s in self.build_constraints(adapter) if not s.is_satisfied)

    def is_satisfied(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> bool:
        """检查所有批次需求是否满足。"""
        return len(self.unsatisfied_demands(adapter)) == 0

    def violations(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[BatchDemandSatisfaction, ...]:
        """获取违反约束的记录。"""
        return self.unsatisfied_demands(adapter)
