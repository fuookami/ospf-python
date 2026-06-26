"""航段定义 / Stowage leg definition.

定义航班中的单个航段及其装载货物。
Defines a single flight leg and its cargo items.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.stowage_item import (
        StowageItem,
    )


@dataclass(frozen=True)
class StowageLeg:
    """航段 / Stowage leg.

    描述航班中的一个航段，包含始发站、目的站和该航段
    需要装载的货物列表。
    Describes a flight leg, including origin, destination,
    and the list of cargo items for that leg.

    Attributes:
        leg_id: 航段标识 / Leg identifier.
        origin: 始发站三字码 / Origin IATA code.
        destination: 目的站三字码 / Destination IATA code.
        items: 该航段的货物列表 / Cargo items for this leg.
    """

    leg_id: str = ""
    """航段标识 / Leg identifier."""

    origin: str = ""
    """始发站三字码 / Origin IATA code."""

    destination: str = ""
    """目的站三字码 / Destination IATA code."""

    items: tuple[StowageItem, ...] = field(
        default_factory=tuple,
    )
    """该航段的货物列表 / Cargo items for this leg."""

    @staticmethod
    def create(
        *,
        leg_id: str,
        origin: str,
        destination: str,
        items: tuple[StowageItem, ...] = (),
    ) -> StowageLeg:
        """创建航段。

        Create stowage leg.

        Args:
            leg_id: 航段标识。/ Leg identifier.
            origin: 始发站三字码。/ Origin IATA code.
            destination: 目的站三字码。/ Destination IATA code.
            items: 货物列表。/ Cargo items.

        Returns:
            航段实例。/ Leg instance.
        """
        return StowageLeg(
            leg_id=leg_id,
            origin=origin,
            destination=destination,
            items=items,
        )

    @property
    def total_weight(self) -> float:
        """该航段货物总重量。

        Total weight of cargo for this leg.

        Returns:
            所有货物重量之和（千克）。
            Sum of all item weights (kg).
        """
        return sum(item.weight for item in self.items)

    @property
    def total_volume(self) -> float:
        """该航段货物总体积。

        Total volume of cargo for this leg.

        Returns:
            所有货物体积之和（立方米）。
            Sum of all item volumes (cubic meters).
        """
        return sum(item.volume for item in self.items)

    @property
    def item_count(self) -> int:
        """货物数量。

        Number of cargo items.

        Returns:
            该航段的货物件数。
            Number of items in this leg.
        """
        return len(self.items)

    def with_item(self, item: StowageItem) -> StowageLeg:
        """添加货物到航段。

        Add an item to the leg.

        Args:
            item: 要添加的货物。/ Item to add.

        Returns:
            包含新货物的航段副本。
            A new leg with the item added.
        """
        return StowageLeg(
            leg_id=self.leg_id,
            origin=self.origin,
            destination=self.destination,
            items=self.items + (item,),
        )

    def items_by_priority(
        self,
    ) -> tuple[StowageItem, ...]:
        """按优先级排序获取货物。

        Get items sorted by priority.

        Returns:
            按优先级从高到低排列的货物元组。
            Items sorted from highest to lowest priority.
        """
        return tuple(
            sorted(
                self.items,
                key=lambda i: i.priority.value,
            )
        )
