"""Gantt scheduling task tail assignment constraint."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskTailAssignmentConstraint:
    """Gantt scheduling task tail assignment constraint."""

    name: str = "task tail assignment constraint"

    def build_constraints(self, model: object, tasks: object) -> tuple[()]:
        """Build solver constraints."""
        return ()

    def is_satisfied(self, schedule: object) -> bool:
        """Check if constraint is satisfied."""
        return True

    def violations(self, schedule: object) -> tuple[()]:
        """Get constraint violations."""
        return ()
