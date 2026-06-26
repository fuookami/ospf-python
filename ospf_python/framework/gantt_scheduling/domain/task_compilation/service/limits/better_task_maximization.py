"""Gantt scheduling better task maximization."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BetterTaskMaximization:
    """Gantt scheduling better task maximization."""

    name: str = "better task maximization"

    def build_objective_terms(self, model: object, tasks: object) -> tuple[()]:
        """Build solver objective terms."""
        return ()

    def compute_value(self, schedule: object) -> float:
        """Compute objective value."""
        return 0.0
