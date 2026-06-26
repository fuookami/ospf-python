"""Crew context for registration and lookup.

机组注册与查找上下文。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from .crew import Crew
    from .crew_member import CrewMember, CrewRole
    from .crew_schedule import CrewSchedule
    from .pilot import Pilot


class CrewContext:
    """Mutable registry for crew data with lookup capabilities.

    支持查找功能的机组数据可变注册表。
    """

    def __init__(self) -> None:
        """Initialize empty crew context.

        初始化空的机组上下文。
        """
        self._crews: dict[str, Crew] = {}
        self._members: dict[str, CrewMember] = {}
        self._pilots: dict[str, Pilot] = {}
        self._schedules: dict[str, CrewSchedule] = {}

    def register_crew(self, crew: Crew) -> None:
        """Register a crew.

        注册机组。

        Args:
            crew: Crew to register.
        """
        self._crews[crew.crew_id] = crew

    def register_member(
        self,
        member: CrewMember,
    ) -> None:
        """Register a crew member.

        注册机组成员。

        Args:
            member: Crew member to register.
        """
        self._members[member.member_id] = member

    def register_pilot(self, pilot: Pilot) -> None:
        """Register a pilot.

        注册飞行员。

        Args:
            pilot: Pilot to register.
        """
        self._pilots[pilot.pilot_id] = pilot

    def register_schedule(
        self,
        schedule: CrewSchedule,
    ) -> None:
        """Register a crew schedule.

        注册机组排班。

        Args:
            schedule: Crew schedule to register.
        """
        self._schedules[schedule.crew_id] = schedule

    def get_crew(
        self,
        crew_id: str,
    ) -> Crew | None:
        """Look up a crew by ID.

        按 ID 查找机组。

        Args:
            crew_id: Unique crew identifier.

        Returns:
            The crew if found, None otherwise.
        """
        return self._crews.get(crew_id)

    def get_member(
        self,
        member_id: str,
    ) -> CrewMember | None:
        """Look up a crew member by ID.

        按 ID 查找机组成员。

        Args:
            member_id: Unique member identifier.

        Returns:
            The crew member if found, None otherwise.
        """
        return self._members.get(member_id)

    def get_pilot(
        self,
        pilot_id: str,
    ) -> Pilot | None:
        """Look up a pilot by ID.

        按 ID 查找飞行员。

        Args:
            pilot_id: Unique pilot identifier.

        Returns:
            The pilot if found, None otherwise.
        """
        return self._pilots.get(pilot_id)

    def get_schedule(
        self,
        crew_id: str,
    ) -> CrewSchedule | None:
        """Look up a crew schedule by crew ID.

        按机组 ID 查找排班。

        Args:
            crew_id: Unique crew identifier.

        Returns:
            The schedule if found, None otherwise.
        """
        return self._schedules.get(crew_id)

    def get_members_by_role(
        self,
        role: CrewRole,
    ) -> Sequence[CrewMember]:
        """Get all members with a given role.

        获取具有给定角色的所有成员。

        Args:
            role: Role to filter by.

        Returns:
            Sequence of matching crew members.
        """
        return tuple(m for m in self._members.values() if m.role == role)

    def get_pilots_for_aircraft(
        self,
        aircraft_type: str,
    ) -> Sequence[Pilot]:
        """Get pilots rated for a specific aircraft type.

        获取有资格驾驶特定飞机类型的飞行员。

        Args:
            aircraft_type: Aircraft type code.

        Returns:
            Sequence of qualified pilots.
        """
        return tuple(p for p in self._pilots.values() if p.can_fly(aircraft_type))

    @property
    def crew_count(self) -> int:
        """Number of registered crews.

        已注册机组数量。
        """
        return len(self._crews)

    @property
    def member_count(self) -> int:
        """Number of registered crew members.

        已注册机组成员数量。
        """
        return len(self._members)
