"""Passenger allocator service.

旅客分配服务。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

from ..model.booking_class import BookingClass
from ..model.passenger_result import (
    PassengerResult,
    PassengerStatus,
)

if TYPE_CHECKING:
    from ..model.passenger import Passenger


@dataclass(frozen=True)
class SeatMap:
    """Seat configuration for an aircraft.

    飞机的座位配置。
    """

    aircraft_type: str
    """Aircraft type code.

    飞机类型代码。
    """

    first_class_rows: int = 0
    """Number of first class rows.

    头等舱排数。
    """

    business_class_rows: int = 0
    """Number of business class rows.

    商务舱排数。
    """

    economy_class_rows: int = 0
    """Number of economy class rows.

    经济舱排数。
    """

    seats_per_row: int = 6
    """Seats per row (A-F typical).

    每排座位数（通常 A-F）。
    """

    @property
    def first_class_capacity(self) -> int:
        """Total first class seats.

        头等舱总座位数。
        """
        return self.first_class_rows * self.seats_per_row

    @property
    def business_class_capacity(self) -> int:
        """Total business class seats.

        商务舱总座位数。
        """
        return self.business_class_rows * self.seats_per_row

    @property
    def economy_class_capacity(self) -> int:
        """Total economy class seats.

        经济舱总座位数。
        """
        return self.economy_class_rows * self.seats_per_row

    @property
    def total_capacity(self) -> int:
        """Total seats on aircraft.

        飞机总座位数。
        """
        return (
            self.first_class_capacity
            + self.business_class_capacity
            + self.economy_class_capacity
        )


@dataclass(frozen=True)
class AllocationResult:
    """Result of passenger seat allocation.

    旅客座位分配的结果。
    """

    results: tuple[PassengerResult, ...] = ()
    """Allocation results per passenger.

    每位旅客的分配结果。
    """

    waitlisted_ids: tuple[str, ...] = ()
    """IDs of waitlisted passengers.

    候补旅客的 ID。
    """

    @property
    def allocated_count(self) -> int:
        """Number of passengers with seats.

        已分配座位的旅客数量。
        """
        return sum(1 for r in self.results if r.has_seat)

    @property
    def waitlisted_count(self) -> int:
        """Number of waitlisted passengers.

        候补旅客数量。
        """
        return len(self.waitlisted_ids)


class PassengerAllocator:
    """Allocates passengers to seats by booking class priority.

    按舱位优先级将旅客分配到座位。
    """

    def __init__(self) -> None:
        """Initialize the passenger allocator.

        初始化旅客分配器。
        """
        self._seat_letters = ("A", "B", "C", "D", "E", "F")

    def allocate(
        self,
        passengers: Sequence[Passenger],
        seat_map: SeatMap,
    ) -> AllocationResult:
        """Allocate passengers to seats.

        将旅客分配到座位。

        Args:
            passengers: Passengers to allocate.
            seat_map: Aircraft seat configuration.

        Returns:
            AllocationResult with seat assignments.
        """
        sorted_pax = sorted(passengers, key=lambda p: p.priority_score)
        counters = {
            BookingClass.FIRST: 1,
            BookingClass.BUSINESS: (seat_map.first_class_rows + 1),
            BookingClass.ECONOMY: (
                seat_map.first_class_rows + seat_map.business_class_rows + 1
            ),
        }
        capacities = {
            BookingClass.FIRST: (seat_map.first_class_capacity),
            BookingClass.BUSINESS: (seat_map.business_class_capacity),
            BookingClass.ECONOMY: (seat_map.economy_class_capacity),
        }
        letter_idx = 0
        results: list[PassengerResult] = []
        waitlisted: list[str] = []
        class_used: dict[BookingClass, int] = {c: 0 for c in BookingClass}

        for pax in sorted_pax:
            cls = pax.booking_class
            if class_used[cls] >= capacities[cls]:
                waitlisted.append(pax.passenger_id)
                results.append(
                    PassengerResult(
                        passenger_id=pax.passenger_id,
                        status=(PassengerStatus.WAITLISTED),
                    )
                )
                continue

            row = counters[cls]
            letter = self._seat_letters[letter_idx % seat_map.seats_per_row]
            seat = f"{row}{letter}"
            letter_idx += 1
            if letter_idx >= seat_map.seats_per_row:
                letter_idx = 0
                counters[cls] += 1

            class_used[cls] += 1
            results.append(
                PassengerResult(
                    passenger_id=pax.passenger_id,
                    status=PassengerStatus.CONFIRMED,
                    seat=seat,
                )
            )

        return AllocationResult(
            results=tuple(results),
            waitlisted_ids=tuple(waitlisted),
        )
