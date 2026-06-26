"""装载方案 / Stowage plan.

定义完整的货物装载方案。
Defines a complete cargo stowage plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.stowage_leg import (
        StowageLeg,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_position import (
        StowagePosition,
    )


@dataclass(frozen=True)
class ItemPlacement:
    """货物放置记录 / Item placement record.

    记录单件货物的放置位置。
    Records the placement of a single cargo item.

    Attributes:
        item_id: 货物标识 / Item identifier.
        position: 放置位置 / Placement position.
        leg_id: 所属航段 / Associated leg.
    """

    item_id: str = ""
    """货物标识 / Item identifier."""

    position: StowagePosition = None  # type: ignore[assignment]
    """放置位置 / Placement position."""

    leg_id: str = ""
    """所属航段 / Associated leg."""


@dataclass(frozen=True)
class StowagePlan:
    """装载方案 / Stowage plan.

    描述一架飞机的完整装载方案，包含航段信息和货物放置。
    Describes a complete stowage plan for an aircraft,
    including leg information and item placements.

    Attributes:
        plan_id: 方案标识 / Plan identifier.
        aircraft_id: 飞机标识 / Aircraft identifier.
        legs: 航段列表 / Leg list.
        total_weight: 总重量（千克）/ Total weight (kg).
        placements: 货物放置记录 / Item placements.
    """

    plan_id: str = ""
    """方案标识 / Plan identifier."""

    aircraft_id: str = ""
    """飞机标识 / Aircraft identifier."""

    legs: tuple[StowageLeg, ...] = field(
        default_factory=tuple,
    )
    """航段列表 / Leg list."""

    total_weight: float = 0.0
    """总重量（千克）/ Total weight (kg)."""

    placements: tuple[ItemPlacement, ...] = field(
        default_factory=tuple,
    )
    """货物放置记录 / Item placements."""

    @staticmethod
    def create(
        *,
        plan_id: str,
        aircraft_id: str,
        legs: tuple[StowageLeg, ...] = (),
        placements: tuple[ItemPlacement, ...] = (),
    ) -> StowagePlan:
        """创建装载方案。

        Create stowage plan.

        Args:
            plan_id: 方案标识。/ Plan identifier.
            aircraft_id: 飞机标识。/ Aircraft identifier.
            legs: 航段列表。/ Leg list.
            placements: 货物放置记录。/ Item placements.

        Returns:
            方案实例。/ Plan instance.
        """
        total = sum(leg.total_weight for leg in legs)
        return StowagePlan(
            plan_id=plan_id,
            aircraft_id=aircraft_id,
            legs=legs,
            total_weight=total,
            placements=placements,
        )

    @property
    def leg_count(self) -> int:
        """航段数量。

        Number of legs.

        Returns:
            航段个数。/ Leg count.
        """
        return len(self.legs)

    @property
    def item_count(self) -> int:
        """货物总数量。

        Total number of cargo items.

        Returns:
            所有航段的货物件数之和。
            Sum of item counts across all legs.
        """
        return sum(leg.item_count for leg in self.legs)

    @property
    def placement_count(self) -> int:
        """放置记录数量。

        Number of placement records.

        Returns:
            放置记录条数。/ Placement record count.
        """
        return len(self.placements)

    def leg_by_id(
        self,
        leg_id: str,
    ) -> StowageLeg | None:
        """按标识查找航段。

        Find leg by identifier.

        Args:
            leg_id: 航段标识。/ Leg identifier.

        Returns:
            匹配的航段，不存在时返回 None。
            Matching leg, or None if not found.
        """
        for leg in self.legs:
            if leg.leg_id == leg_id:
                return leg
        return None

    def placements_for_leg(
        self,
        leg_id: str,
    ) -> tuple[ItemPlacement, ...]:
        """获取指定航段的所有放置记录。

        Get all placements for a specific leg.

        Args:
            leg_id: 航段标识。/ Leg identifier.

        Returns:
            匹配的放置记录元组。/ Tuple of matching placements.
        """
        return tuple(p for p in self.placements if p.leg_id == leg_id)

    def with_placement(
        self,
        placement: ItemPlacement,
    ) -> StowagePlan:
        """添加放置记录。

        Add a placement record.

        Args:
            placement: 放置记录。/ Placement record.

        Returns:
            包含新记录的方案副本。
            A new plan with the placement added.
        """
        return StowagePlan(
            plan_id=self.plan_id,
            aircraft_id=self.aircraft_id,
            legs=self.legs,
            total_weight=self.total_weight,
            placements=self.placements + (placement,),
        )
