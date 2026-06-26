"""Gantt scheduling produce order constraint."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProduceOrderConstraint:
    """Gantt scheduling produce order constraint."""

    name: str = "produce order constraint"

    def build_constraints(self, model: object, tasks: object) -> tuple[()]:
        """Build solver constraints."""
        return ()

    def is_satisfied(self, schedule: object) -> bool:
        """Check if constraint is satisfied."""
        return True

    def violations(self, schedule: object) -> tuple[()]:
        """Get constraint violations."""
        return ()
