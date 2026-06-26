"""卸载顺序约束。

Access sequence constraint ensuring unload accessibility.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AccessSequenceItem:
    """卸载顺序物品信息。

    Item with its required unload sequence position.

    Attributes:
        item_id: 物品标识 / Item identifier
        unload_order: 卸载顺序（越小越先卸）/ Unload order (lower = earlier)
        compartment_id: 所在舱室 / Assigned compartment
    """

    item_id: str
    unload_order: int
    compartment_id: str


@dataclass(frozen=True)
class AccessSequenceConstraint:
    """卸载顺序可达性约束。

    Enforces that items with earlier unload sequence are physically
    accessible (not blocked by items that unload later).

    Attributes:
        compartments: 舱室列表 / List of compartment IDs
    """

    compartments: tuple[str, ...]

    def evaluate(
        self,
        items: tuple[AccessSequenceItem, ...],
    ) -> tuple[bool, list[str]]:
        """评估卸载顺序可达性。

        For each compartment, checks that items are arranged so that
        earlier-unload items are not blocked by later-unload items.

        Args:
            items: 所有装载物品 / All loaded items with sequence info

        Returns:
            tuple: (是否满足, 违规描述) / (satisfied, violation descriptions)
        """
        violations: list[str] = []
        by_compartment: dict[str, list[AccessSequenceItem]] = {}
        for item in items:
            by_compartment.setdefault(item.compartment_id, []).append(item)

        for comp_id in self.compartments:
            comp_items = by_compartment.get(comp_id, [])
            sorted_items = sorted(comp_items, key=lambda x: x.unload_order)
            for i in range(len(sorted_items) - 1):
                current = sorted_items[i]
                next_item = sorted_items[i + 1]
                if current.unload_order > next_item.unload_order:
                    violations.append(
                        f"舱室 {comp_id}: 物品 {current.item_id} "
                        f"(顺序{current.unload_order}) 被 "
                        f"{next_item.item_id} (顺序{next_item.unload_order}) "
                        f"阻挡"
                    )

        return (len(violations) == 0, violations)

    def sort_for_loading(
        self,
        items: tuple[AccessSequenceItem, ...],
    ) -> tuple[AccessSequenceItem, ...]:
        """按卸载顺序的逆序排列（后卸的先装）。

        Sorts items in reverse unload order so that the last-to-unload
        items are placed first (deepest in compartment).

        Args:
            items: 待排序物品 / Items to sort

        Returns:
            tuple: 按装载顺序排列的物品 / Items in loading order
        """
        return tuple(sorted(items, key=lambda x: x.unload_order, reverse=True))
