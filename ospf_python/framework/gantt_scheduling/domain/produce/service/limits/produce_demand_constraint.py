"""Gantt scheduling produce demand constraint."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProduceDemandConstraint:
    """Gantt scheduling produce demand constraint."""

    name: str = "produce demand constraint"

    def build_constraints(self, model, tasks):
        """Build solver constraints."""
        return ()

    def is_satisfied(self, schedule):
        """Check if constraint is satisfied."""
        return True

    def violations(self, schedule):
        """Get constraint violations."""
        return ()
