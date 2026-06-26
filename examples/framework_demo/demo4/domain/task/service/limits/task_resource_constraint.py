"""Task resource constraint.

任务资源约束。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from ...model.task_requirement import TaskRequirement


class TaskResourceConstraint:
    """Enforces resource availability constraints.

    执行资源可用性约束。
    """

    def __init__(
        self,
        *,
        total_aircraft: dict[str, int],
        total_crew: dict[str, int],
    ) -> None:
        """Initialize resource constraint.

        初始化资源约束。

        Args:
            total_aircraft: Available count per aircraft type.
            total_crew: Available count per crew qualification.
        """
        self._total_aircraft = dict(total_aircraft)
        self._total_crew = dict(total_crew)

    def validate_aircraft(
        self,
        requirements: Sequence[TaskRequirement],
    ) -> Sequence[str]:
        """Validate aircraft availability for requirements.

        验证需求的飞机可用性。

        Args:
            requirements: Task requirements to check.

        Returns:
            Violation descriptions (empty if valid).
        """
        demand: dict[str, int] = {}
        for req in requirements:
            demand[req.aircraft_type] = demand.get(req.aircraft_type, 0) + 1

        violations: list[str] = []
        for aircraft_type, needed in demand.items():
            available = self._total_aircraft.get(aircraft_type, 0)
            if needed > available:
                violations.append(f"{aircraft_type}: need {needed}, have {available}")

        return tuple(violations)

    def validate_crew(
        self,
        requirements: Sequence[TaskRequirement],
    ) -> Sequence[str]:
        """Validate crew availability for requirements.

        验证需求的机组可用性。

        Args:
            requirements: Task requirements to check.

        Returns:
            Violation descriptions (empty if valid).
        """
        total_crew_needed = sum(r.crew_count for r in requirements)
        total_available = sum(self._total_crew.values())

        violations: list[str] = []
        if total_crew_needed > total_available:
            violations.append(f"Crew: need {total_crew_needed}, have {total_available}")

        return tuple(violations)

    def validate(
        self,
        requirements: Sequence[TaskRequirement],
    ) -> Sequence[str]:
        """Validate all resource constraints.

        验证所有资源约束。

        Args:
            requirements: Task requirements to check.

        Returns:
            All violation descriptions.
        """
        aircraft_violations = self.validate_aircraft(requirements)
        crew_violations = self.validate_crew(requirements)
        return list(aircraft_violations) + list(crew_violations)

    def is_feasible(
        self,
        requirements: Sequence[TaskRequirement],
    ) -> bool:
        """Check if requirements can be satisfied.

        检查需求是否可满足。

        Args:
            requirements: Task requirements to check.

        Returns:
            True if all resources are available.
        """
        return len(self.validate(requirements)) == 0
