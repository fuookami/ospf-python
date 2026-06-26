"""Crew duty time constraint.

机组执勤时间约束。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from ...model.crew_schedule import CrewSchedule


class CrewDutyTimeConstraint:
    """Enforces maximum duty time limits.

    执行最长执勤时间限制。
    """

    def __init__(
        self,
        *,
        max_duty_hours: float = 14.0,
        max_duty_hours_extended: float = 16.0,
        max_weekly_hours: float = 60.0,
    ) -> None:
        """Initialize duty time constraint.

        初始化执勤时间约束。

        Args:
            max_duty_hours: Standard max duty hours.
            max_duty_hours_extended: Extended max with
                rest requirement.
            max_weekly_hours: Max cumulative weekly hours.
        """
        self._max_duty = max_duty_hours
        self._max_duty_extended = max_duty_hours_extended
        self._max_weekly = max_weekly_hours

    def validate(
        self,
        schedules: Sequence[CrewSchedule],
    ) -> Sequence[str]:
        """Validate duty time limits in schedules.

        验证排班中的执勤时间限制。

        Args:
            schedules: Crew schedules to validate.

        Returns:
            Violation descriptions (empty if valid).
        """
        violations: list[str] = []

        for schedule in schedules:
            total = schedule.total_duty_hours
            if total > self._max_duty:
                violations.append(
                    f"Crew {schedule.crew_id}: "
                    f"duty {total:.1f}h > "
                    f"{self._max_duty}h limit"
                )

            for assignment in schedule.assignments:
                if assignment.duration_hours > self._max_duty_extended:
                    violations.append(
                        f"Crew {schedule.crew_id}: "
                        f"single assignment "
                        f"{assignment.duration_hours:.1f}h"
                        f" > {self._max_duty_extended}h"
                    )

        return tuple(violations)

    def is_valid(
        self,
        schedules: Sequence[CrewSchedule],
    ) -> bool:
        """Check if all duty times are within limits.

        检查所有执勤时间是否在限制内。

        Args:
            schedules: Crew schedules to check.

        Returns:
            True if all duty times are acceptable.
        """
        return len(self.validate(schedules)) == 0

    def remaining_duty_hours(
        self,
        schedule: CrewSchedule,
    ) -> float:
        """Calculate remaining duty hours for a crew.

        计算机组的剩余执勤小时。

        Args:
            schedule: Current crew schedule.

        Returns:
            Remaining duty hours available.
        """
        return max(
            0.0,
            self._max_duty - schedule.total_duty_hours,
        )
