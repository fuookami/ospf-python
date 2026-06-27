"""资源需求约束 / Resource demand constraint.

确保每个资源的需求得到满足。
Ensures that each resource's demand is satisfied.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_solver_value_adapter import (
        TaskCompilationSolverValueAdapter,
    )


@dataclass(frozen=True)
class ResourceDemandSatisfaction:
    """资源需求满足状态 / Resource demand satisfaction status.

    Attributes:
        resource_key: 资源标识 / Resource identifier.
        is_satisfied: 是否已满足 / Whether satisfied.
        required_amount: 需求量 / Required amount.
        assigned_amount: 已分配量 / Assigned amount.
        shortfall: 缺口量 / Shortfall amount.
    """

    resource_key: str
    is_satisfied: bool
    required_amount: float
    assigned_amount: float
    shortfall: float


@dataclass(frozen=True)
class ResourceDemandConstraint:
    """资源需求约束 / Resource demand constraint.

    生成资源需求约束数据，确保每个资源的总需求量在可用
    容量范围内得到满足。
    Generates resource demand constraint data, ensuring each
    resource's total demand is satisfied within available
    capacity.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "resource_demand"

    def build_constraints(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[ResourceDemandSatisfaction, ...]:
        """构建资源需求约束列表。

        Build the list of resource demand constraints.

        Args:
            adapter: 求解器值适配器。/ Solver value adapter.

        Returns:
            资源需求满足状态元组。
            Tuple of resource demand satisfaction data.
        """
        results: list[ResourceDemandSatisfaction] = []
        for res_key in adapter.resource_keys:
            required = adapter.total_required(res_key)
            assigned = adapter.total_assigned(res_key)
            shortfall = max(0.0, required - assigned)
            results.append(
                ResourceDemandSatisfaction(
                    resource_key=res_key,
                    is_satisfied=shortfall <= 1e-9,
                    required_amount=required,
                    assigned_amount=assigned,
                    shortfall=shortfall,
                )
            )
        return tuple(results)

    def constraint_name(self, resource_key: str) -> str:
        """生成约束名称。"""
        return f"{self.constraint_name_prefix}_{resource_key}"

    def unsatisfied_demands(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[ResourceDemandSatisfaction, ...]:
        """获取所有未满足的资源需求。"""
        return tuple(s for s in self.build_constraints(adapter) if not s.is_satisfied)

    def is_satisfied(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> bool:
        """检查所有资源需求是否满足。"""
        return len(self.unsatisfied_demands(adapter)) == 0

    def violations(
        self,
        adapter: TaskCompilationSolverValueAdapter,
    ) -> tuple[ResourceDemandSatisfaction, ...]:
        """获取违反约束的记录。"""
        return self.unsatisfied_demands(adapter)
