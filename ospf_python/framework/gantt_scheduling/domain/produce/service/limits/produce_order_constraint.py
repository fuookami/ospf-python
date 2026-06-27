"""生产排序约束 / Produce order constraint.

确保生产物料项之间的排序关系得到满足。
Ensures that ordering relationships between production
items are satisfied.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.produce.model.produce_aggregation import (
        ProduceAggregation,
    )


@dataclass(frozen=True)
class ProduceOrderPair:
    """生产排序对 / Produce order pair.

    表示两个物料项之间的排序关系。
    Represents an ordering relationship between two items.

    Attributes:
        predecessor_key: 前序物料项标识 / Predecessor item id.
        successor_key: 后序物料项标识 / Successor item id.
        is_satisfied: 排序是否满足 / Whether order is satisfied.
        predecessor_end: 前序结束时间 / Predecessor end time.
        successor_start: 后序开始时间 / Successor start time.
    """

    predecessor_key: str
    successor_key: str
    is_satisfied: bool
    predecessor_end: float = 0.0
    successor_start: float = 0.0


@dataclass(frozen=True)
class ProduceOrderConstraint:
    """生产排序约束 / Produce order constraint.

    生成生产排序约束数据，确保有依赖关系的物料项按照规定的
    先后顺序进行生产。适用于需要保证前序物料完成生产后才能
    开始后续物料生产的场景。
    Generates produce order constraint data, ensuring items
    with dependencies are produced in the specified sequence.
    Applicable when predecessor items must finish before
    successor items can begin.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "produce_order"

    def build_constraints(
        self,
        aggregation: ProduceAggregation,
    ) -> tuple[ProduceOrderPair, ...]:
        """构建生产排序约束列表。

        Build the list of produce order constraints.

        遍历所有排序对，检查前序物料项的结束时间是否不晚于
        后序物料项的开始时间。
        Iterates over all order pairs, verifying that each
        predecessor finishes no later than its successor starts.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.

        Returns:
            排序约束数据元组。/ Tuple of order constraint data.
        """
        constraints: list[ProduceOrderPair] = []
        for order in aggregation.order_pairs:
            pred_assignments = aggregation.assignments_for_item(
                order.predecessor_key,
            )
            succ_assignments = aggregation.assignments_for_item(
                order.successor_key,
            )
            pred_end = max(
                (a.end_time for a in pred_assignments),
                default=0.0,
            )
            succ_start = min(
                (a.start_time for a in succ_assignments),
                default=float("inf"),
            )
            is_ok = pred_end <= succ_start + 1e-9
            constraints.append(
                ProduceOrderPair(
                    predecessor_key=order.predecessor_key,
                    successor_key=order.successor_key,
                    is_satisfied=is_ok,
                    predecessor_end=pred_end,
                    successor_start=succ_start,
                )
            )
        return tuple(constraints)

    def constraint_name(
        self,
        *,
        predecessor_key: str,
        successor_key: str,
    ) -> str:
        """生成约束名称。

        Generate the constraint name.

        Args:
            predecessor_key: 前序标识。/ Predecessor id.
            successor_key: 后序标识。/ Successor id.

        Returns:
            约束名称字符串。/ Constraint name string.
        """
        return f"{self.constraint_name_prefix}_{predecessor_key}_{successor_key}"

    def is_satisfied(
        self,
        aggregation: ProduceAggregation,
    ) -> bool:
        """检查所有排序约束是否满足。

        Check whether all order constraints are satisfied.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.

        Returns:
            若所有排序约束均可满足则返回 True。
            True if all order constraints can be satisfied.
        """
        return all(pair.is_satisfied for pair in self.build_constraints(aggregation))

    def violations(
        self,
        aggregation: ProduceAggregation,
    ) -> tuple[ProduceOrderPair, ...]:
        """获取所有违反排序约束的记录。

        Get all records that violate order constraints.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.

        Returns:
            违反约束的排序对元组。
            Tuple of order pairs violating constraints.
        """
        return tuple(
            pair
            for pair in self.build_constraints(aggregation)
            if not pair.is_satisfied
        )
