"""Passenger model.

旅客模型。
"""

from __future__ import annotations

from dataclasses import dataclass

from .booking_class import BookingClass


@dataclass(frozen=True)
class Passenger:
    """A passenger with booking and connection information.

    具有预订和中转信息的旅客。
    """

    passenger_id: str
    """Unique identifier for the passenger.

    旅客的唯一标识符。
    """

    name: str
    """Passenger's full name.

    旅客的全名。
    """

    booking_class: BookingClass
    """Booked cabin class.

    预订的舱位等级。
    """

    connecting_flight: str | None = None
    """Connecting flight number, if any.

    中转航班号（如有）。
    """

    @property
    def is_first_class(self) -> bool:
        """Whether passenger is in first class.

        旅客是否在头等舱。
        """
        return self.booking_class == BookingClass.FIRST

    @property
    def is_business_class(self) -> bool:
        """Whether passenger is in business class.

        旅客是否在商务舱。
        """
        return self.booking_class == BookingClass.BUSINESS

    @property
    def has_connection(self) -> bool:
        """Whether passenger has a connecting flight.

        旅客是否有中转航班。
        """
        return self.connecting_flight is not None

    @property
    def priority_score(self) -> int:
        """Priority score (lower is higher priority).

        优先级分数（越低优先级越高）。
        """
        return self.booking_class.value
