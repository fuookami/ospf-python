"""束编组需求约束 / Bunch demand constraint.

确保每个物料项的束编组需求得到满足。
Ensures that each material item's bunch demand is satisfied.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.bunch_compilation_aggregation import (
        BunchCompilationAggregation,
    )


@dataclass(frozen=True)
class DemandSatisfaction:
    """需求满足状态 / Demand satisfaction status.

    Attributes:
        item_key: 物料项标识 / Item identifier.
        is_satisfied: 是否已满足 / Whether satisfied.
        assigned_ratio: 已分配比例 / Assigned ratio.
        shortfall: 缺口量 / Shortfall amount.
    """

    item_key: str
    is_satisfied: bool
    assigned_ratio: float
    shortfall: float


@dataclass(frozen=True)
class BunchDemandConstraint:
    """束编组需求约束 / Bunch demand constraint.

    生成束编组需求约束数据，确保每个物料项被完全分配到
    束编组中。支持刚性需求（必须完全分配）和柔性需求
    （允许部分分配）。
    Generates bunch demand constraint data, ensuring each
    material item is fully assigned to bunch groups. Supports
    mandatory demands (must be fully assigned) and flexible
    demands (partial assignment allowed).

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
        required_ratio: 要求的分配比例，默认 1.0 (完全分配) /
            Required assignment ratio, default 1.0 (full).
    """

    constraint_name_prefix: str = "bunch_demand"
    required_ratio: float = 1.0

    def build_constraints(
        self,
        aggregation: BunchCompilationAggregation,
    ) -> tuple[DemandSatisfaction, ...]:
        """构建束编组需求约束列表。

        Build the list of bunch demand constraints.

        遍历所有物料项，检查每个物料项的总分配比例是否
        满足要求。
        Iterates over all items, checking whether each item's
        total assignment ratio meets the requirement.

        Args:
            aggregation: 束编组聚合。/ Bunch compilation aggregation.

        Returns:
            需求满足状态元组。/ Tuple of demand satisfaction statuses.
        """
        results: list[DemandSatisfaction] = []
        for item_key in aggregation.item_keys:
            item_assignments = aggregation.assignments_for_item(
                item_key,
            )
            total_ratio = sum(a.assignment_ratio for a in item_assignments)
            shortfall = max(0.0, self.required_ratio - total_ratio)
            results.append(
                DemandSatisfaction(
                    item_key=item_key,
                    is_satisfied=shortfall <= 1e-9,
                    assigned_ratio=total_ratio,
                    shortfall=shortfall,
                )
            )
        return tuple(results)

    def constraint_name(
        self,
        item_key: str,
    ) -> str:
        """生成约束名称。

        Generate the constraint name.

        Args:
            item_key: 物料项标识。/ Item identifier.

        Returns:
            约束名称字符串。/ Constraint name string.
        """
        return f"{self.constraint_name_prefix}_{item_key}"

    def unsatisfied_demands(
        self,
        aggregation: BunchCompilationAggregation,
    ) -> tuple[DemandSatisfaction, ...]:
        """获取所有未满足的需求。

        Get all unsatisfied demands.

        Args:
            aggregation: 束编组聚合。/ Bunch compilation aggregation.

        Returns:
            未满足的需求元组。/ Tuple of unsatisfied demands.
        """
        return tuple(
            s for s in self.build_constraints(aggregation) if not s.is_satisfied
        )

    def is_feasible(
        self,
        aggregation: BunchCompilationAggregation,
    ) -> bool:
        """检查所有需求是否可行。

        Check whether all demands are feasible.

        Args:
            aggregation: 束编组聚合。/ Bunch compilation aggregation.

        Returns:
            若所有需求均可满足则返回 True。
            True if all demands can be satisfied.
        """
        return len(self.unsatisfied_demands(aggregation)) == 0
