"""装载结果 / Stowage result.

封装装载方案的评估结果。
Encapsulates the evaluation result of a stowage plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.stowage_plan import (
        StowagePlan,
    )


@dataclass(frozen=True)
class Penalty:
    """惩罚项 / Penalty.

    记录一条约束违反的惩罚信息。
    Records penalty information for a constraint violation.

    Attributes:
        constraint_type: 违反的约束类型 /
            Violated constraint type.
        penalty_value: 惩罚值 / Penalty value.
        description: 违反描述 / Violation description.
    """

    constraint_type: str = ""
    """违反的约束类型 / Violated constraint type."""

    penalty_value: float = 0.0
    """惩罚值 / Penalty value."""

    description: str = ""
    """违反描述 / Violation description."""


@dataclass(frozen=True)
class StowageResult:
    """装载结果 / Stowage result.

    封装装载方案的可行性评估和惩罚信息。
    Encapsulates feasibility assessment and penalty information
    for a stowage plan.

    Attributes:
        plan: 装载方案 / Stowage plan.
        feasibility: 可行性评分（0.0=不可行, 1.0=完全可行）/
            Feasibility score (0.0=infeasible, 1.0=fully feasible).
        penalties: 惩罚项列表 / Penalty list.
    """

    plan: StowagePlan = None  # type: ignore[assignment]
    """装载方案 / Stowage plan."""

    feasibility: float = 0.0
    """可行性评分（0.0-1.0）/ Feasibility score (0.0-1.0)."""

    penalties: tuple[Penalty, ...] = field(
        default_factory=tuple,
    )
    """惩罚项列表 / Penalty list."""

    @staticmethod
    def feasible(plan: StowagePlan) -> StowageResult:
        """创建可行结果。

        Create feasible result.

        Args:
            plan: 装载方案。/ Stowage plan.

        Returns:
            可行性为 1.0 的结果实例。
            Result instance with feasibility 1.0.
        """
        return StowageResult(
            plan=plan,
            feasibility=1.0,
            penalties=(),
        )

    @staticmethod
    def infeasible(
        plan: StowagePlan,
        penalties: tuple[Penalty, ...],
    ) -> StowageResult:
        """创建不可行结果。

        Create infeasible result.

        Args:
            plan: 装载方案。/ Stowage plan.
            penalties: 惩罚项。/ Penalties.

        Returns:
            可行性为 0.0 的结果实例。
            Result instance with feasibility 0.0.
        """
        return StowageResult(
            plan=plan,
            feasibility=0.0,
            penalties=penalties,
        )

    @property
    def is_feasible(self) -> bool:
        """是否可行。

        Whether the plan is feasible.

        Returns:
            可行性评分为 1.0 时返回 True。
            True if feasibility score is 1.0.
        """
        return self.feasibility >= 1.0

    @property
    def total_penalty(self) -> float:
        """总惩罚值。

        Total penalty value.

        Returns:
            所有惩罚项的惩罚值之和。
            Sum of all penalty values.
        """
        return sum(p.penalty_value for p in self.penalties)

    @property
    def penalty_count(self) -> int:
        """惩罚项数量。

        Number of penalties.

        Returns:
            惩罚项条数。/ Penalty count.
        """
        return len(self.penalties)

    def penalties_by_type(
        self,
        constraint_type: str,
    ) -> tuple[Penalty, ...]:
        """按类型获取惩罚项。

        Get penalties by constraint type.

        Args:
            constraint_type: 约束类型。/ Constraint type.

        Returns:
            匹配的惩罚项元组。/ Tuple of matching penalties.
        """
        return tuple(p for p in self.penalties if p.constraint_type == constraint_type)

    def with_penalty(self, penalty: Penalty) -> StowageResult:
        """添加惩罚项。

        Add a penalty.

        Args:
            penalty: 惩罚项。/ Penalty.

        Returns:
            包含新惩罚项的结果副本。
            A new result with the penalty added.
        """
        return StowageResult(
            plan=self.plan,
            feasibility=self.feasibility,
            penalties=self.penalties + (penalty,),
        )
