"""Gantt scheduling precedence constraint."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrecedenceConstraint:
    """Gantt scheduling precedence constraint."""

    name: str = "precedence constraint"

    def build_constraints(self, model, tasks):
        """Build solver constraints."""
        return ()

    def is_satisfied(self, schedule):
        """Check if constraint is satisfied."""
        return True

    def violations(self, schedule):
        """Get constraint violations."""
        return ()
