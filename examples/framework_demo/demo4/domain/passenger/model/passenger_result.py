"""Passenger result model.

旅客结果模型。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique


@unique
class PassengerStatus(Enum):
    """Status of a passenger's booking.

    旅客预订的状态。
    """

    CONFIRMED = "CONFIRMED"
    """Booking is confirmed.

    预订已确认。
    """

    WAITLISTED = "WAITLISTED"
    """Passenger is on waitlist.

    旅客在候补名单上。
    """

    CHECKED_IN = "CHECKED_IN"
    """Passenger has checked in.

    旅客已办理登机。
    """

    BOARDED = "BOARDED"
    """Passenger has boarded the aircraft.

    旅客已登机。
    """

    CANCELLED = "CANCELLED"
    """Booking has been cancelled.

    预订已被取消。
    """


@dataclass(frozen=True)
class PassengerResult:
    """Result of passenger seat allocation.

    旅客座位分配的结果。
    """

    passenger_id: str
    """ID of the passenger.

    旅客的 ID。
    """

    status: PassengerStatus
    """Current booking status.

    当前预订状态。
    """

    seat: str | None = None
    """Assigned seat number (e.g. '12A').

    分配的座位号（如 '12A'）。
    """

    @property
    def is_confirmed(self) -> bool:
        """Whether the booking is confirmed.

        预订是否已确认。
        """
        return self.status == PassengerStatus.CONFIRMED

    @property
    def has_seat(self) -> bool:
        """Whether a seat has been assigned.

        是否已分配座位。
        """
        return self.seat is not None

    @property
    def seat_row(self) -> int | None:
        """Extracted seat row number.

        提取的座位排号。
        """
        if self.seat is None:
            return None
        digits = ""
        for char in self.seat:
            if char.isdigit():
                digits += char
            else:
                break
        return int(digits) if digits else None

    @property
    def seat_letter(self) -> str | None:
        """Extracted seat letter.

        提取的座位字母。
        """
        if self.seat is None:
            return None
        for char in self.seat:
            if char.isalpha():
                return char
        return None
