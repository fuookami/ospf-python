"""优先级排序约束。

Priority ordering constraint enforcing loading sequence by priority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...model.loading_priority import LoadingPriority


@dataclass(frozen=True)
class PriorityItem:
    """优先级物品信息。

    Item with its loading priority and position.

    Attributes:
        item_id: 物品标识 / Item identifier
        priority: 装载优先级 / Loading priority
        loading_position: 装载位置序号 / Loading position sequence number
    """

    item_id: str
    priority: LoadingPriority
    loading_position: int


@dataclass(frozen=True)
class PriorityConstraint:
    """优先级排序约束。

    Enforces that higher-priority items are loaded in positions
    that give them better access (lower position numbers = loaded
    later but more accessible, or earlier depending on convention).

    Attributes:
        strict: 是否严格排序 / Whether strict ordering is required
    """

    strict: bool

    def evaluate(
        self,
        items: tuple[PriorityItem, ...],
    ) -> tuple[bool, list[str]]:
        """评估优先级排序约束。

        Checks that items are loaded in the correct priority order.
        Higher priority items should have lower loading position numbers.

        Args:
            items: 所有优先级物品 / All priority items

        Returns:
            tuple: (是否满足, 违规描述) / (satisfied, violation descriptions)
        """
        violations: list[str] = []
        sorted_by_position = sorted(items, key=lambda x: x.loading_position)

        for i in range(len(sorted_by_position) - 1):
            current = sorted_by_position[i]
            next_item = sorted_by_position[i + 1]
            if self.strict:
                if current.priority.value > next_item.priority.value:
                    violations.append(
                        f"位置 {current.loading_position}: "
                        f"{current.item_id} ({current.priority.label_zh()}) "
                        f"优先级低于位置 {next_item.loading_position}: "
                        f"{next_item.item_id} ({next_item.priority.label_zh()})"
                    )
            else:
                priority_gap = next_item.priority.value - current.priority.value
                if priority_gap < -1:
                    violations.append(
                        f"位置 {current.loading_position}: "
                        f"{current.item_id} 优先级 {current.priority.label_zh()} "
                        f"显著低于 {next_item.item_id} "
                        f"优先级 {next_item.priority.label_zh()}"
                    )

        return (len(violations) == 0, violations)

    def suggested_order(
        self,
        items: tuple[PriorityItem, ...],
    ) -> tuple[PriorityItem, ...]:
        """建议按优先级排列的装载顺序。

        Returns items sorted by priority (highest first), then by
        original position for equal priorities.

        Args:
            items: 待排序物品 / Items to sort

        Returns:
            tuple: 按优先级排序的物品 / Items in priority order
        """
        return tuple(
            sorted(items, key=lambda x: (x.priority.value, x.loading_position))
        )
