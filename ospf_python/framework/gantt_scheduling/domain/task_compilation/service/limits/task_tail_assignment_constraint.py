"""Gantt scheduling task tail assignment constraint."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskTailAssignmentConstraint:
    """Gantt scheduling task tail assignment constraint."""

    name: str = "task tail assignment constraint"

    def build_constraints(self, model, tasks):
        """Build solver constraints."""
        return ()

    def is_satisfied(self, schedule):
        """Check if constraint is satisfied."""
        return True

    def violations(self, schedule):
        """Get constraint violations."""
        return ()
