"""Crew schedule model.

机组排班模型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class CrewAssignment:
    """A single crew assignment to a flight.

    机组对单个航班的任务分配。
    """

    task_id: str
    """ID of the assigned flight task.

    被分配航班任务的 ID。
    """

    member_id: str
    """ID of the assigned crew member.

    被分配机组成员的 ID。
    """

    start_time: datetime
    """Assignment start time.

    任务分配开始时间。
    """

    end_time: datetime
    """Assignment end time.

    任务分配结束时间。
    """

    @property
    def duration_hours(self) -> float:
        """Assignment duration in hours.

        任务分配持续时间（小时）。
        """
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600.0


@dataclass(frozen=True)
class RestPeriod:
    """A rest period between assignments.

    任务分配间的休息时段。
    """

    member_id: str
    """ID of the crew member.

    机组成员的 ID。
    """

    start_time: datetime
    """Rest period start time.

    休息时段开始时间。
    """

    end_time: datetime
    """Rest period end time.

    休息时段结束时间。
    """

    @property
    def duration_hours(self) -> float:
        """Rest duration in hours.

        休息持续时间（小时）。
        """
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600.0

    @property
    def is_minimum_rest(self) -> bool:
        """Whether rest meets minimum 8-hour requirement.

        休息是否满足最低 8 小时要求。
        """
        return self.duration_hours >= 8.0


@dataclass(frozen=True)
class CrewSchedule:
    """Schedule for a crew with assignments and rest periods.

    包含任务分配和休息时段的机组排班。
    """

    crew_id: str
    """ID of the crew.

    机组的 ID。
    """

    assignments: tuple[CrewAssignment, ...] = field(default_factory=tuple)
    """Flight assignments for this crew.

    此机组的航班分配。
    """

    rest_periods: tuple[RestPeriod, ...] = field(default_factory=tuple)
    """Rest periods between assignments.

    任务分配间的休息时段。
    """

    @property
    def assignment_count(self) -> int:
        """Number of flight assignments.

        航班分配数量。
        """
        return len(self.assignments)

    @property
    def total_duty_hours(self) -> float:
        """Total duty time in hours.

        总执勤时间（小时）。
        """
        return sum(a.duration_hours for a in self.assignments)

    @property
    def has_adequate_rest(self) -> bool:
        """Whether all rest periods meet minimum requirements.

        所有休息时段是否满足最低要求。
        """
        return all(r.is_minimum_rest for r in self.rest_periods)

    @property
    def first_assignment(
        self,
    ) -> CrewAssignment | None:
        """The earliest assignment, if any.

        最早的任务分配（如有）。
        """
        if not self.assignments:
            return None
        return min(self.assignments, key=lambda a: a.start_time)

    @property
    def last_assignment(
        self,
    ) -> CrewAssignment | None:
        """The latest assignment, if any.

        最晚的任务分配（如有）。
        """
        if not self.assignments:
            return None
        return max(self.assignments, key=lambda a: a.end_time)
