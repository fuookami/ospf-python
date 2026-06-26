"""Crew qualification constraint.

机组资质约束。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from ...model.crew_member import CrewRole

if TYPE_CHECKING:
    from ...model.crew import Crew
    from ...model.pilot import Pilot


class CrewQualificationConstraint:
    """Enforces crew qualification requirements.

    执行机组资质要求。
    """

    def __init__(
        self,
        *,
        require_atpl_for_captain: bool = True,
        min_captain_hours: int = 3000,
        min_first_officer_hours: int = 1500,
    ) -> None:
        """Initialize qualification constraint.

        初始化资质约束。

        Args:
            require_atpl_for_captain: Captain must hold ATPL.
            min_captain_hours: Min flight hours for captain.
            min_first_officer_hours: Min hours for first
                officer.
        """
        self._require_atpl = require_atpl_for_captain
        self._min_captain_hours = min_captain_hours
        self._min_fo_hours = min_first_officer_hours

    def validate_pilot(
        self,
        pilot: Pilot,
        role: CrewRole,
        aircraft_type: str,
    ) -> Sequence[str]:
        """Validate a pilot's qualifications.

        验证飞行员的资质。

        Args:
            pilot: Pilot to validate.
            role: Assigned role.
            aircraft_type: Aircraft type to fly.

        Returns:
            Violation descriptions (empty if valid).
        """
        violations: list[str] = []

        if not pilot.can_fly(aircraft_type):
            violations.append(f"Pilot {pilot.pilot_id}: not rated for {aircraft_type}")

        if role == CrewRole.CAPTAIN and self._require_atpl and not pilot.is_atpl:
            violations.append(f"Pilot {pilot.pilot_id}: captain requires ATPL license")

        if role == CrewRole.CAPTAIN and pilot.flight_hours < self._min_captain_hours:
            violations.append(
                f"Pilot {pilot.pilot_id}: captain "
                f"needs {self._min_captain_hours}h, "
                f"has {pilot.flight_hours}h"
            )

        if role == CrewRole.FIRST_OFFICER and pilot.flight_hours < self._min_fo_hours:
            violations.append(
                f"Pilot {pilot.pilot_id}: FO needs "
                f"{self._min_fo_hours}h, "
                f"has {pilot.flight_hours}h"
            )

        return tuple(violations)

    def validate_crew(
        self,
        crew: Crew,
        aircraft_type: str,
    ) -> Sequence[str]:
        """Validate crew qualifications for aircraft.

        验证机组对飞机的资质。

        Args:
            crew: Crew to validate.
            aircraft_type: Aircraft type needed.

        Returns:
            Violation descriptions (empty if valid).
        """
        violations: list[str] = []

        if not crew.is_qualified_for(aircraft_type):
            violations.append(f"Crew {crew.crew_id}: not qualified for {aircraft_type}")

        return tuple(violations)

    def is_pilot_qualified(
        self,
        pilot: Pilot,
        role: CrewRole,
        aircraft_type: str,
    ) -> bool:
        """Check if pilot meets all qualification requirements.

        检查飞行员是否满足所有资质要求。

        Args:
            pilot: Pilot to check.
            role: Assigned role.
            aircraft_type: Aircraft type to fly.

        Returns:
            True if pilot is fully qualified.
        """
        return len(self.validate_pilot(pilot, role, aircraft_type)) == 0
