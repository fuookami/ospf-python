"""Passenger amount model.

旅客数量模型。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .booking_class import BookingClass


@dataclass(frozen=True)
class PassengerAmount:
    """Passenger count for a specific flight and class.

    特定航班和舱位的旅客计数。
    """

    flight_no: str
    """Flight number.

    航班号。
    """

    class_type: BookingClass
    """Booking class.

    预订舱位。
    """

    count: int
    """Number of passengers.

    旅客数量。
    """

    @property
    def is_empty(self) -> bool:
        """Whether the count is zero.

        数量是否为零。
        """
        return self.count == 0

    @property
    def is_positive(self) -> bool:
        """Whether there are passengers.

        是否有旅客。
        """
        return self.count > 0

    @property
    def display_label(self) -> str:
        """Human-readable label.

        人类可读的标签。
        """
        return f"{self.flight_no} {self.class_type.display_name}: {self.count}"
