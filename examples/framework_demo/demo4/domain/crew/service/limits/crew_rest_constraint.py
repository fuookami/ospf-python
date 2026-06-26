"""Crew rest period constraint.

机组休息时段约束。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from ...model.crew_schedule import CrewSchedule


class CrewRestConstraint:
    """Enforces minimum rest period requirements.

    执行最低休息时段要求。
    """

    def __init__(
        self,
        *,
        min_rest_hours: float = 8.0,
        min_rest_between_flights: float = 10.0,
    ) -> None:
        """Initialize rest constraint.

        初始化休息约束。

        Args:
            min_rest_hours: Minimum rest hours after duty.
            min_rest_between_flights: Min rest between
                consecutive flights.
        """
        self._min_rest_hours = min_rest_hours
        self._min_rest_between = min_rest_between_flights

    def validate(
        self,
        schedules: Sequence[CrewSchedule],
    ) -> Sequence[str]:
        """Validate rest periods in crew schedules.

        验证机组排班中的休息时段。

        Args:
            schedules: Crew schedules to validate.

        Returns:
            Violation descriptions (empty if valid).
        """
        violations: list[str] = []

        for schedule in schedules:
            for rest in schedule.rest_periods:
                if rest.duration_hours < self._min_rest_hours:
                    violations.append(
                        f"Crew {schedule.crew_id}: "
                        f"rest {rest.duration_hours:.1f}h"
                        f" < {self._min_rest_hours}h "
                        f"minimum"
                    )

        return tuple(violations)

    def is_valid(
        self,
        schedules: Sequence[CrewSchedule],
    ) -> bool:
        """Check if all rest periods meet requirements.

        检查所有休息时段是否满足要求。

        Args:
            schedules: Crew schedules to check.

        Returns:
            True if all rest periods are adequate.
        """
        return len(self.validate(schedules)) == 0

    def calculate_min_rest(
        self,
        duty_hours: float,
    ) -> float:
        """Calculate minimum required rest for given duty.

        计算给定执勤时间的最低所需休息。

        Args:
            duty_hours: Hours of duty time.

        Returns:
            Minimum rest hours required.
        """
        if duty_hours > 12.0:
            return self._min_rest_hours * 1.5
        if duty_hours > 8.0:
            return self._min_rest_hours * 1.25
        return self._min_rest_hours
