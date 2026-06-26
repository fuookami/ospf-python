"""Passenger context for registration and lookup.

旅客注册与查找上下文。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from .passenger_aggregation import PassengerAggregation

if TYPE_CHECKING:
    from .booking_class import BookingClass
    from .passenger import Passenger
    from .passenger_cancel import PassengerCancel
    from .passenger_result import PassengerResult


class PassengerContext:
    """Mutable registry for passenger data.

    旅客数据的可变注册表。
    """

    def __init__(self) -> None:
        """Initialize empty passenger context.

        初始化空的旅客上下文。
        """
        self._passengers: dict[str, Passenger] = {}
        self._results: dict[str, PassengerResult] = {}
        self._cancellations: dict[str, PassengerCancel] = {}

    def register_passenger(
        self,
        passenger: Passenger,
    ) -> None:
        """Register a passenger.

        注册旅客。

        Args:
            passenger: Passenger to register.
        """
        self._passengers[passenger.passenger_id] = passenger

    def register_result(
        self,
        result: PassengerResult,
    ) -> None:
        """Register a passenger result.

        注册旅客结果。

        Args:
            result: Passenger result to register.
        """
        self._results[result.passenger_id] = result

    def register_cancellation(
        self,
        cancel: PassengerCancel,
    ) -> None:
        """Register a passenger cancellation.

        注册旅客取消。

        Args:
            cancel: Cancellation record to register.
        """
        self._cancellations[cancel.passenger_id] = cancel

    def get_passenger(
        self,
        passenger_id: str,
    ) -> Passenger | None:
        """Look up a passenger by ID.

        按 ID 查找旅客。

        Args:
            passenger_id: Unique passenger identifier.

        Returns:
            The passenger if found, None otherwise.
        """
        return self._passengers.get(passenger_id)

    def get_result(
        self,
        passenger_id: str,
    ) -> PassengerResult | None:
        """Look up a passenger result by ID.

        按 ID 查找旅客结果。

        Args:
            passenger_id: Unique passenger identifier.

        Returns:
            The result if found, None otherwise.
        """
        return self._results.get(passenger_id)

    def get_cancellation(
        self,
        passenger_id: str,
    ) -> PassengerCancel | None:
        """Look up a cancellation by passenger ID.

        按旅客 ID 查找取消记录。

        Args:
            passenger_id: Unique passenger identifier.

        Returns:
            The cancellation if found, None otherwise.
        """
        return self._cancellations.get(passenger_id)

    def get_passengers_by_class(
        self,
        booking_class: BookingClass,
    ) -> Sequence[Passenger]:
        """Get all passengers in a booking class.

        获取某舱位的所有旅客。

        Args:
            booking_class: Class to filter by.

        Returns:
            Sequence of matching passengers.
        """
        return tuple(
            p for p in self._passengers.values() if p.booking_class == booking_class
        )

    def get_connecting_passengers(
        self,
    ) -> Sequence[Passenger]:
        """Get all passengers with connecting flights.

        获取所有有中转航班的旅客。

        Returns:
            Sequence of connecting passengers.
        """
        return tuple(p for p in self._passengers.values() if p.has_connection)

    def build_aggregation(
        self,
    ) -> PassengerAggregation:
        """Build an aggregation of all registered passengers.

        构建所有已注册旅客的聚合。

        Returns:
            PassengerAggregation grouped by class.
        """
        return PassengerAggregation.from_passengers(list(self._passengers.values()))

    @property
    def passenger_count(self) -> int:
        """Number of registered passengers.

        已注册旅客数量。
        """
        return len(self._passengers)
