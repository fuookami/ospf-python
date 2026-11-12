"""生产批次排序约束 / Produce batch order constraint.

确保生产批次之间的排序关系得到满足。
Ensures that ordering relationships between production
batches are satisfied.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.produce.model.produce_aggregation import (
        ProduceAggregation,
    )


@dataclass(frozen=True)
class BatchOrderPair:
    """批次排序对 / Batch order pair.

    表示两个批次之间的排序关系。
    Represents an ordering relationship between two batches.

    Attributes:
        predecessor_key: 前序批次标识 / Predecessor batch id.
        successor_key: 后序批次标识 / Successor batch id.
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
class ProduceBatchOrderConstraint:
    """生产批次排序约束 / Produce batch order constraint.

    生成生产批次排序约束数据，确保有依赖关系的批次按照规定
    的先后顺序进行生产。适用于需要保证前序批次完成后才能
    开始后续批次生产的场景。
    Generates produce batch order constraint data, ensuring
    batches with dependencies are produced in the specified
    sequence. Applicable when predecessor batches must finish
    before successor batches can begin.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "produce_batch_order"

    def build_constraints(
        self,
        aggregation: ProduceAggregation,
    ) -> tuple[BatchOrderPair, ...]:
        """构建批次排序约束列表。

        Build the list of batch order constraints.

        遍历所有批次排序对，检查前序批次的结束时间是否不晚于
        后序批次的开始时间。
        Iterates over all batch order pairs, verifying that each
        predecessor finishes no later than its successor starts.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.

        Returns:
            排序约束数据元组。/ Tuple of order constraint data.

        一次遍历把每个批次的「最晚结束 / 最早开始」算好，而不是对每个排序对
        各调用两次 `assignments_for_batch`（那是 O(对数 × 分配)）。
        `max(...)` / `min(...)` 的取值与改前相同（空集合分别得 0.0 与 +inf）。

        Precompute each batch's latest end and earliest start in one pass instead of
        calling `assignments_for_batch` twice per order pair (O(pairs x assignments)).
        The max/min values match the previous behaviour, including the empty cases.
        """
        assignments_raw = getattr(aggregation, "assignments", None)
        latest_end: dict[str, float] = {}
        earliest_start: dict[str, float] = {}
        if assignments_raw is not None:
            for assignment in assignments_raw:
                key = getattr(assignment, "batch_key", None)
                if key is None:
                    continue
                end_time = getattr(assignment, "end_time", 0.0)
                start_time = getattr(assignment, "start_time", 0.0)
                if key not in latest_end or end_time > latest_end[key]:
                    latest_end[key] = end_time
                if key not in earliest_start or start_time < earliest_start[key]:
                    earliest_start[key] = start_time

        constraints: list[BatchOrderPair] = []
        for order in aggregation.batch_order_pairs:
            if assignments_raw is None:
                pred_end = max(
                    (
                        a.end_time
                        for a in aggregation.assignments_for_batch(
                            order.predecessor_key
                        )
                    ),
                    default=0.0,
                )
                succ_start = min(
                    (
                        a.start_time
                        for a in aggregation.assignments_for_batch(
                            order.successor_key
                        )
                    ),
                    default=float("inf"),
                )
            else:
                pred_end = latest_end.get(order.predecessor_key, 0.0)
                succ_start = earliest_start.get(order.successor_key, float("inf"))
            is_ok = pred_end <= succ_start + 1e-9
            constraints.append(
                BatchOrderPair(
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
        """检查所有批次排序约束是否满足。

        Check whether all batch order constraints are satisfied.

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
    ) -> tuple[BatchOrderPair, ...]:
        """获取所有违反批次排序约束的记录。

        Get all records that violate batch order constraints.

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
