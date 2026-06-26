"""Passenger aggregation model.

旅客聚合模型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Sequence

from .booking_class import BookingClass

if TYPE_CHECKING:
    from .passenger import Passenger


@dataclass(frozen=True)
class PassengerAggregation:
    """Aggregated view of passengers grouped by class.

    按舱位分组的旅客聚合视图。
    """

    passengers: tuple[Passenger, ...] = ()
    """All passengers in the aggregation.

    聚合中的所有旅客。
    """

    by_class: dict[BookingClass, tuple[Passenger, ...]] = field(default_factory=dict)
    """Passengers grouped by booking class.

    按预订舱位分组的旅客。
    """

    @property
    def total_count(self) -> int:
        """Total number of passengers.

        旅客总数。
        """
        return len(self.passengers)

    @property
    def first_class_count(self) -> int:
        """Number of first class passengers.

        头等舱旅客数量。
        """
        return len(self.by_class.get(BookingClass.FIRST, ()))

    @property
    def business_class_count(self) -> int:
        """Number of business class passengers.

        商务舱旅客数量。
        """
        return len(self.by_class.get(BookingClass.BUSINESS, ()))

    @property
    def economy_class_count(self) -> int:
        """Number of economy class passengers.

        经济舱旅客数量。
        """
        return len(self.by_class.get(BookingClass.ECONOMY, ()))

    @property
    def connecting_count(self) -> int:
        """Number of passengers with connections.

        有中转的旅客数量。
        """
        return sum(1 for p in self.passengers if p.has_connection)

    @property
    def premium_ratio(self) -> float:
        """Ratio of premium (first + business) passengers.

        高级舱位（头等 + 商务）旅客比例。
        """
        if self.total_count == 0:
            return 0.0
        premium = self.first_class_count + self.business_class_count
        return premium / self.total_count

    @classmethod
    def from_passengers(
        cls,
        passengers: Sequence[Passenger],
    ) -> PassengerAggregation:
        """Build aggregation from a passenger sequence.

        从旅客序列构建聚合。

        Args:
            passengers: Passengers to aggregate.

        Returns:
            New PassengerAggregation grouped by class.
        """
        pax_tuple = tuple(passengers)
        by_class: dict[BookingClass, list[Passenger]] = {}

        for pax in pax_tuple:
            by_class.setdefault(pax.booking_class, []).append(pax)

        return cls(
            passengers=pax_tuple,
            by_class={k: tuple(v) for k, v in by_class.items()},
        )
