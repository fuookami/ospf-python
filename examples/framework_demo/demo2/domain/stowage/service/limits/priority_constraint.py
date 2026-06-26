"""优先级约束 / Priority constraint.

确保高优先级货物先于低优先级货物装载。
Ensures that higher priority items are loaded before
lower priority items.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.stowage_item import (
        StowageItem,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_priority import (
        StowagePriority,
    )


@dataclass(frozen=True)
class PriorityViolation:
    """优先级违反记录 / Priority violation record.

    记录低优先级货物被排在高优先级货物之前的信息。
    Records a lower priority item being loaded before a
    higher priority item.

    Attributes:
        higher_item: 高优先级货物标识 /
            Higher priority item identifier.
        lower_item: 低优先级货物标识 /
            Lower priority item identifier.
        higher_position: 高优先级货物的位置 /
            Position of higher priority item.
        lower_position: 低优先级货物的位置 /
            Position of lower priority item.
    """

    higher_item: str = ""
    """高优先级货物标识 / Higher priority item identifier."""

    lower_item: str = ""
    """低优先级货物标识 / Lower priority item identifier."""

    higher_position: int = 0
    """高优先级货物的位置 / Position of higher priority item."""

    lower_position: int = 0
    """低优先级货物的位置 / Position of lower priority item."""


@dataclass(frozen=True)
class PriorityConstraint:
    """优先级约束 / Priority constraint.

    验证装载顺序尊重货物的优先级。高优先级货物必须在
    低优先级货物之前装载，相同优先级的货物可以任意顺序。
    Validates that loading order respects item priority.
    Higher priority items must be loaded before lower priority
    items; items with equal priority may be in any order.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
        strict: 是否严格模式（相同优先级也需排序）/
            Strict mode (equal priority also ordered).
    """

    constraint_name_prefix: str = "priority"
    """约束名称前缀 / Constraint name prefix."""

    strict: bool = False
    """是否严格模式 / Strict mode."""

    def check_order(
        self,
        *,
        items: tuple[StowageItem, ...],
        loading_order: dict[str, int],
    ) -> tuple[PriorityViolation, ...]:
        """检查装载顺序是否满足优先级要求。

        Check whether loading order satisfies priority requirements.

        Args:
            items: 货物列表。/ Item list.
            loading_order: 装载顺序映射。/ Loading order mapping.

        Returns:
            违反记录元组。/ Tuple of violation records.
        """
        violations: list[PriorityViolation] = []
        indexed = [
            (item, loading_order.get(item.item_id))
            for item in items
            if item.item_id in loading_order
        ]
        for i, (item_a, pos_a) in enumerate(indexed):
            for item_b, pos_b in indexed[i + 1 :]:
                if pos_a is None or pos_b is None:
                    continue
                dominated = item_a.priority.dominates(
                    item_b.priority,
                )
                if dominated and pos_a > pos_b:
                    violations.append(
                        PriorityViolation(
                            higher_item=item_a.item_id,
                            lower_item=item_b.item_id,
                            higher_position=pos_a,
                            lower_position=pos_b,
                        )
                    )
                elif self.strict:
                    reverse = item_b.priority.dominates(
                        item_a.priority,
                    )
                    if reverse and pos_b > pos_a:
                        violations.append(
                            PriorityViolation(
                                higher_item=item_b.item_id,
                                lower_item=item_a.item_id,
                                higher_position=pos_b,
                                lower_position=pos_a,
                            )
                        )
        return tuple(violations)

    def is_feasible(
        self,
        *,
        items: tuple[StowageItem, ...],
        loading_order: dict[str, int],
    ) -> bool:
        """检查优先级约束是否可行。

        Check whether priority constraints are feasible.

        Args:
            items: 货物列表。/ Item list.
            loading_order: 装载顺序映射。/ Loading order mapping.

        Returns:
            所有优先级要求均满足时返回 True。
            True if all priority requirements are satisfied.
        """
        return (
            len(
                self.check_order(
                    items=items,
                    loading_order=loading_order,
                )
            )
            == 0
        )

    def suggest_order(
        self,
        items: tuple[StowageItem, ...],
    ) -> tuple[str, ...]:
        """建议按优先级排序的装载顺序。

        Suggest loading order by priority.

        Args:
            items: 货物列表。/ Item list.

        Returns:
            按优先级排序的货物标识元组。
            Item identifiers sorted by priority.
        """
        sorted_items = sorted(
            items,
            key=lambda i: (i.priority.value, i.item_id),
        )
        return tuple(item.item_id for item in sorted_items)

    def priority_groups(
        self,
        items: tuple[StowageItem, ...],
    ) -> dict[StowagePriority, tuple[str, ...]]:
        """按优先级分组货物。

        Group items by priority.

        Args:
            items: 货物列表。/ Item list.

        Returns:
            优先级到货物标识的映射。
            Mapping from priority to item identifiers.
        """
        groups: dict[StowagePriority, list[str]] = {}
        for item in items:
            groups.setdefault(item.priority, []).append(
                item.item_id,
            )
        return {k: tuple(v) for k, v in groups.items()}
