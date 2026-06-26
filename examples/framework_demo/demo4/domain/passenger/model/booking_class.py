"""Booking class enumeration.

预订舱位枚举。
"""

from __future__ import annotations

from enum import IntEnum, unique


@unique
class BookingClass(IntEnum):
    """Passenger booking class with priority ordering.

    具有优先级排序的旅客预订舱位。
    """

    FIRST = 0
    """First class cabin.

    头等舱。
    """

    BUSINESS = 1
    """Business class cabin.

    商务舱。
    """

    ECONOMY = 2
    """Economy class cabin.

    经济舱。
    """

    @property
    def display_name(self) -> str:
        """Human-readable display name.

        人类可读的显示名称。
        """
        return {
            BookingClass.FIRST: "First Class",
            BookingClass.BUSINESS: "Business Class",
            BookingClass.ECONOMY: "Economy Class",
        }[self]

    @property
    def code(self) -> str:
        """Short booking class code.

        短预订舱位代码。
        """
        return {
            BookingClass.FIRST: "F",
            BookingClass.BUSINESS: "J",
            BookingClass.ECONOMY: "Y",
        }[self]
