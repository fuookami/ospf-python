"""束编组容量约束 / Bunch capacity constraint.

确保每个束编组在任意时间窗口内的使用量不超过其容量上限。
Ensures that each bunch's usage within any time window does
not exceed its capacity upper bound.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.capacity import (
    BunchCapacity,
)

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.bunch_compilation_aggregation import (
        BunchCompilationAggregation,
    )


@dataclass(frozen=True)
class BunchCapacityConstraint:
    """束编组容量约束 / Bunch capacity constraint.

    生成束编组容量约束数据，用于注册到优化模型中。每条约束
    确保在指定时间窗口内，所有物料项对束编组的需求总量不
    超过束编组容量上限。
    Generates bunch capacity constraint data for registration
    into the optimization model. Each constraint ensures that
    within a given time window, the total demand from all items
    on a bunch does not exceed the bunch capacity upper bound.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "bunch_capacity"

    def build_constraints(
        self,
        aggregation: BunchCompilationAggregation,
    ) -> tuple[BunchCapacity, ...]:
        """构建束编组容量约束列表。

        Build the list of bunch capacity constraints.

        遍历所有已注册束编组和容量记录，校验每个束编组内
        的需求总量是否在容量范围内。
        Iterates over all registered bunches and capacity records,
        verifying that total demand within each bunch is within
        capacity bounds.

        Args:
            aggregation: 束编组聚合。/ Bunch compilation aggregation.

        Returns:
            容量约束数据元组。/ Tuple of capacity constraint data.
        """
        constraints: list[BunchCapacity] = []
        for cap in aggregation.capacities:
            total_demand = aggregation.total_demand_for_bunch(
                cap.bunch_key,
            )
            constraints.append(
                BunchCapacity(
                    bunch_key=cap.bunch_key,
                    time_window_start=cap.time_window_start,
                    time_window_end=cap.time_window_end,
                    max_capacity=cap.max_capacity,
                    used_capacity=total_demand,
                )
            )
        return tuple(constraints)

    def constraint_name(
        self,
        bunch_key: str,
    ) -> str:
        """生成约束名称。

        Generate the constraint name.

        Args:
            bunch_key: 束编组标识。/ Bunch identifier.

        Returns:
            约束名称字符串。/ Constraint name string.
        """
        return f"{self.constraint_name_prefix}_{bunch_key}"

    def is_feasible(
        self,
        aggregation: BunchCompilationAggregation,
    ) -> bool:
        """检查容量约束是否可行。

        Check whether capacity constraints are feasible.

        Args:
            aggregation: 束编组聚合。/ Bunch compilation aggregation.

        Returns:
            若所有容量约束均可满足则返回 True。
            True if all capacity constraints can be satisfied.
        """
        for cap in self.build_constraints(aggregation):
            if cap.used_capacity > cap.max_capacity:
                return False
        return True

    def violations(
        self,
        aggregation: BunchCompilationAggregation,
    ) -> tuple[BunchCapacity, ...]:
        """获取所有违反容量约束的记录。

        Get all records that violate capacity constraints.

        Args:
            aggregation: 束编组聚合。/ Bunch compilation aggregation.

        Returns:
            违反约束的容量记录元组。
            Tuple of capacity records violating constraints.
        """
        return tuple(
            cap
            for cap in self.build_constraints(aggregation)
            if cap.used_capacity > cap.max_capacity
        )
