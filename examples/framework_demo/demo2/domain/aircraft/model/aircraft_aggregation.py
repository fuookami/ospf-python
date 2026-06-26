"""航空器聚合定义 / Aircraft aggregation definition.

管理多个航空器实例的聚合查询。
Aggregation query for multiple aircraft instances.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.aircraft.model.aircraft import Aircraft


@dataclass(frozen=True)
class AircraftAggregation:
    """航空器聚合 / Aircraft aggregation.

    将多个航空器实例聚合为一个集合，提供便捷的
    查询和筛选方法。
    Aggregates multiple aircraft instances into a collection
    with convenient query and filter methods.

    Attributes:
        aircraft: 航空器元组 / Tuple of aircraft.
    """

    aircraft: tuple[Aircraft, ...]
    """航空器元组 / Tuple of aircraft."""

    @staticmethod
    def create(
        *,
        aircraft: tuple[Aircraft, ...],
    ) -> AircraftAggregation:
        """创建航空器聚合 / Create aircraft aggregation.

        Args:
            aircraft: 航空器元组 / Tuple of aircraft.

        Returns:
            航空器聚合实例 / Aircraft aggregation instance.
        """
        return AircraftAggregation(aircraft=aircraft)

    @staticmethod
    def empty() -> AircraftAggregation:
        """创建空聚合 / Create empty aggregation.

        Returns:
            空的航空器聚合 / Empty aircraft aggregation.
        """
        return AircraftAggregation(aircraft=())

    @property
    def count(self) -> int:
        """航空器数量 / Number of aircraft.

        Returns:
            航空器数量 / Aircraft count.
        """
        return len(self.aircraft)

    @property
    def is_empty(self) -> bool:
        """是否为空 / Whether aggregation is empty.

        Returns:
            无航空器时为 True / True if no aircraft.
        """
        return len(self.aircraft) == 0

    def by_type(self, aircraft_type: str) -> tuple[Aircraft, ...]:
        """按机型筛选 / Filter by aircraft type.

        Args:
            aircraft_type: 机型代码 / Aircraft type code.

        Returns:
            匹配机型的航空器元组 / Matching aircraft tuple.
        """
        return tuple(a for a in self.aircraft if a.aircraft_type == aircraft_type)

    def by_registration(self, registration: str) -> Aircraft | None:
        """按注册号查找 / Lookup by registration.

        Args:
            registration: 注册号 / Registration number.

        Returns:
            匹配的航空器或 None / Matching aircraft or None.
        """
        for a in self.aircraft:
            if a.registration == registration:
                return a
        return None

    def with_deck_count(self, deck_count: int) -> tuple[Aircraft, ...]:
        """按甲板层数筛选 / Filter by deck count.

        Args:
            deck_count: 甲板层数 / Number of decks.

        Returns:
            匹配甲板层数的航空器元组 / Matching aircraft tuple.
        """
        return tuple(a for a in self.aircraft if a.deck_count == deck_count)

    def heaviest_capacity(self) -> Aircraft | None:
        """获取最大起飞重量的航空器 / Get aircraft with highest takeoff weight.

        Returns:
            最大起飞重量的航空器或 None /
            Aircraft with highest MTOW or None.
        """
        if not self.aircraft:
            return None
        return max(self.aircraft, key=lambda a: a.max_takeoff_weight)

    def largest_cargo_volume(self) -> Aircraft | None:
        """获取最大货舱体积的航空器 / Get aircraft with largest cargo volume.

        Returns:
            最大货舱体积的航空器或 None /
            Aircraft with largest cargo volume or None.
        """
        if not self.aircraft:
            return None
        return max(self.aircraft, key=lambda a: a.cargo_hold_volume)

    def add(self, aircraft: Aircraft) -> AircraftAggregation:
        """添加航空器（返回新聚合）/ Add aircraft (returns new aggregation).

        Args:
            aircraft: 待添加的航空器 / Aircraft to add.

        Returns:
            包含新航空器的新聚合 / New aggregation with added aircraft.
        """
        return AircraftAggregation(
            aircraft=self.aircraft + (aircraft,),
        )

    def remove(self, registration: str) -> AircraftAggregation:
        """移除航空器（返回新聚合）/ Remove aircraft (returns new aggregation).

        Args:
            registration: 待移除航空器的注册号 / Registration to remove.

        Returns:
            移除后的新聚合 / New aggregation after removal.
        """
        return AircraftAggregation(
            aircraft=tuple(a for a in self.aircraft if a.registration != registration),
        )
