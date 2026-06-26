"""Crew allocator service.

机组分配服务。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Sequence

from ..model.crew_member import CrewMember, CrewRole
from ..model.crew_schedule import (
    CrewAssignment,
    CrewSchedule,
    RestPeriod,
)

if TYPE_CHECKING:
    from ..model.crew import Crew


@dataclass(frozen=True)
class CrewAllocation:
    """Result of allocating crew to a flight.

    将机组分配给航班的结果。
    """

    task_id: str
    """ID of the flight task.

    航班任务的 ID。
    """

    crew_id: str
    """ID of the assigned crew.

    被分配机组的 ID。
    """

    member_ids: tuple[str, ...] = ()
    """IDs of assigned crew members.

    被分配机组成员的 ID。
    """

    @property
    def member_count(self) -> int:
        """Number of assigned members.

        被分配成员数量。
        """
        return len(self.member_ids)


@dataclass(frozen=True)
class CrewAllocationResult:
    """Result of a crew allocation operation.

    机组分配操作的结果。
    """

    allocations: tuple[CrewAllocation, ...] = ()
    """Successful allocations.

    成功的分配。
    """

    unallocated_task_ids: tuple[str, ...] = ()
    """Tasks that could not be crewed.

    无法配备机组的任务。
    """

    @property
    def all_allocated(self) -> bool:
        """Whether all tasks received crew.

        是否所有任务都已配备机组。
        """
        return len(self.unallocated_task_ids) == 0


class CrewAllocator:
    """Allocates crew members to flight tasks.

    将机组成员分配给航班任务。
    """

    def __init__(self) -> None:
        """Initialize the crew allocator.

        初始化机组分配器。
        """
        self._min_rest_hours = 8.0
        self._max_duty_hours = 14.0

    def allocate(
        self,
        tasks: Sequence[tuple[str, str]],
        available_crews: Sequence[Crew],
        available_members: Sequence[CrewMember],
        *,
        base_time: datetime,
    ) -> CrewAllocationResult:
        """Allocate crew to flight tasks.

        将机组分配给航班任务。

        Args:
            tasks: Sequence of (task_id, aircraft_type).
            available_crews: Available crews.
            available_members: Available crew members.
            base_time: Reference time for scheduling.

        Returns:
            CrewAllocationResult with allocations.
        """
        crew_map = {c.crew_id: c for c in available_crews}
        member_pool = list(available_members)
        allocations: list[CrewAllocation] = []
        unallocated: list[str] = []

        for task_id, aircraft_type in tasks:
            assigned = self._assign_members(
                aircraft_type,
                member_pool,
            )
            if assigned is None:
                unallocated.append(task_id)
                continue

            crew_id = self._find_matching_crew(
                aircraft_type,
                crew_map,
            )
            if crew_id is None:
                crew_id = f"adhoc-{task_id}"

            allocations.append(
                CrewAllocation(
                    task_id=task_id,
                    crew_id=crew_id,
                    member_ids=tuple(m.member_id for m in assigned),
                )
            )

        return CrewAllocationResult(
            allocations=tuple(allocations),
            unallocated_task_ids=tuple(unallocated),
        )

    def _assign_members(
        self,
        aircraft_type: str,
        pool: list[CrewMember],
    ) -> list[CrewMember] | None:
        """Assign members from pool for an aircraft type.

        从池中为飞机类型分配成员。

        Args:
            aircraft_type: Aircraft type needing crew.
            pool: Available member pool (mutated).

        Returns:
            Assigned members, or None if insufficient.
        """
        captain = self._pop_role(pool, CrewRole.CAPTAIN)
        first_officer = self._pop_role(pool, CrewRole.FIRST_OFFICER)
        if captain is None or first_officer is None:
            if captain is not None:
                pool.append(captain)
            if first_officer is not None:
                pool.append(first_officer)
            return None

        cabin_chief = self._pop_role(pool, CrewRole.CABIN_CHIEF)
        attendants = [self._pop_role(pool, CrewRole.CABIN_ATTENDANT) for _ in range(2)]

        result: list[CrewMember] = [
            captain,
            first_officer,
        ]
        if cabin_chief is not None:
            result.append(cabin_chief)
        for att in attendants:
            if att is not None:
                result.append(att)

        return result

    def _pop_role(
        self,
        pool: list[CrewMember],
        role: CrewRole,
    ) -> CrewMember | None:
        """Remove and return first member with given role.

        移除并返回第一个具有给定角色的成员。

        Args:
            pool: Member pool to search (mutated).
            role: Role to find.

        Returns:
            Matching member, or None if not found.
        """
        for i, member in enumerate(pool):
            if member.role == role:
                return pool.pop(i)
        return None

    def _find_matching_crew(
        self,
        aircraft_type: str,
        crew_map: dict[str, Crew],
    ) -> str | None:
        """Find a crew qualified for the aircraft type.

        查找有资格操作该飞机类型的机组。

        Args:
            aircraft_type: Aircraft type code.
            crew_map: Available crews by ID.

        Returns:
            Crew ID if found, None otherwise.
        """
        for crew in crew_map.values():
            if crew.is_qualified_for(aircraft_type):
                return crew.crew_id
        return None

    def build_schedule(
        self,
        crew_id: str,
        assignments: Sequence[CrewAssignment],
    ) -> CrewSchedule:
        """Build a crew schedule with rest periods.

        构建包含休息时段的机组排班。

        Args:
            crew_id: Crew ID for the schedule.
            assignments: Flight assignments.

        Returns:
            CrewSchedule with calculated rest periods.
        """
        sorted_assignments = sorted(assignments, key=lambda a: a.start_time)
        rest_periods: list[RestPeriod] = []

        for i in range(len(sorted_assignments) - 1):
            current = sorted_assignments[i]
            next_assign = sorted_assignments[i + 1]
            rest = RestPeriod(
                member_id=crew_id,
                start_time=current.end_time,
                end_time=next_assign.start_time,
            )
            rest_periods.append(rest)

        return CrewSchedule(
            crew_id=crew_id,
            assignments=tuple(sorted_assignments),
            rest_periods=tuple(rest_periods),
        )
