"""Passenger capacity constraint.

旅客容量约束。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from ...model.booking_class import BookingClass

if TYPE_CHECKING:
    from ...model.passenger_amount import PassengerAmount


class PassengerCapacityConstraint:
    """Enforces aircraft seat capacity limits.

    执行飞机座位容量限制。
    """

    def __init__(
        self,
        *,
        first_class_capacity: int = 12,
        business_class_capacity: int = 40,
        economy_class_capacity: int = 150,
    ) -> None:
        """Initialize capacity constraint.

        初始化容量约束。

        Args:
            first_class_capacity: Max first class seats.
            business_class_capacity: Max business seats.
            economy_class_capacity: Max economy seats.
        """
        self._capacities = {
            BookingClass.FIRST: first_class_capacity,
            BookingClass.BUSINESS: (business_class_capacity),
            BookingClass.ECONOMY: (economy_class_capacity),
        }

    def validate(
        self,
        amounts: Sequence[PassengerAmount],
    ) -> Sequence[str]:
        """Validate passenger counts against capacity.

        根据容量验证旅客数量。

        Args:
            amounts: Passenger amounts per flight/class.

        Returns:
            Violation descriptions (empty if valid).
        """
        by_class: dict[BookingClass, int] = {c: 0 for c in BookingClass}

        for amount in amounts:
            by_class[amount.class_type] = (
                by_class.get(amount.class_type, 0) + amount.count
            )

        violations: list[str] = []
        for cls, total in by_class.items():
            cap = self._capacities.get(cls, 0)
            if total > cap:
                violations.append(
                    f"{cls.display_name}: {total} passengers exceed {cap} capacity"
                )

        return tuple(violations)

    def is_within_capacity(
        self,
        amounts: Sequence[PassengerAmount],
    ) -> bool:
        """Check if passenger counts fit within capacity.

        检查旅客数量是否在容量内。

        Args:
            amounts: Passenger amounts to check.

        Returns:
            True if all classes are within capacity.
        """
        return len(self.validate(amounts)) == 0

    def remaining_capacity(
        self,
        booking_class: BookingClass,
        current_count: int,
    ) -> int:
        """Calculate remaining capacity for a class.

        计算某舱位的剩余容量。

        Args:
            booking_class: Class to check.
            current_count: Current passenger count.

        Returns:
            Remaining seats available.
        """
        cap = self._capacities.get(booking_class, 0)
        return max(0, cap - current_count)
