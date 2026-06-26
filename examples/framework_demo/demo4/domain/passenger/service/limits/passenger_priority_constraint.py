"""Passenger priority constraint.

旅客优先级约束。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from ...model.booking_class import BookingClass
from ...model.passenger_result import (
    PassengerResult,
    PassengerStatus,
)

if TYPE_CHECKING:
    from ...model.passenger import Passenger


class PassengerPriorityConstraint:
    """Enforces booking class priority during allocation.

    在分配期间执行舱位优先级。
    """

    def __init__(
        self,
        *,
        bump_lower_class: bool = False,
    ) -> None:
        """Initialize priority constraint.

        初始化优先级约束。

        Args:
            bump_lower_class: Whether lower class can be
                bumped to accommodate higher class.
        """
        self._bump_lower = bump_lower_class

    def validate_allocation_order(
        self,
        passengers: Sequence[Passenger],
        results: Sequence[PassengerResult],
    ) -> Sequence[str]:
        """Validate that higher class got seats first.

        验证高舱位旅客优先获得座位。

        Args:
            passengers: Original passenger list.
            results: Allocation results.

        Returns:
            Violation descriptions (empty if valid).
        """
        result_map = {r.passenger_id: r for r in results}
        violations: list[str] = []

        by_class: dict[BookingClass, list[Passenger]] = {c: [] for c in BookingClass}
        for pax in passengers:
            by_class[pax.booking_class].append(pax)

        lower_waitlisted = 0
        for cls in BookingClass:
            for pax in by_class[cls]:
                result = result_map.get(pax.passenger_id)
                if result is None:
                    continue
                if result.status == PassengerStatus.WAITLISTED:
                    lower_waitlisted += 1
            if lower_waitlisted > 0:
                break

        higher_waitlisted = 0
        for cls in reversed(list(BookingClass)):
            for pax in by_class[cls]:
                result = result_map.get(pax.passenger_id)
                if result is None:
                    continue
                if result.status == PassengerStatus.WAITLISTED:
                    higher_waitlisted += 1

        if higher_waitlisted > 0 and lower_waitlisted == 0:
            violations.append(
                "Higher class passengers waitlisted "
                "while lower class passengers have seats"
            )

        return tuple(violations)

    def sort_by_priority(
        self,
        passengers: Sequence[Passenger],
    ) -> Sequence[Passenger]:
        """Sort passengers by booking class priority.

        按舱位优先级对旅客排序。

        Args:
            passengers: Passengers to sort.

        Returns:
            Passengers sorted by class (first class first).
        """
        return tuple(
            sorted(
                passengers,
                key=lambda p: p.priority_score,
            )
        )

    def should_bump(
        self,
        displaced_class: BookingClass,
        requesting_class: BookingClass,
    ) -> bool:
        """Check if a lower class should be bumped.

        检查是否应挤掉低舱位旅客。

        Args:
            displaced_class: Class being displaced.
            requesting_class: Class requesting the seat.

        Returns:
            True if bumping is allowed.
        """
        if not self._bump_lower:
            return False
        return requesting_class.value < displaced_class.value
