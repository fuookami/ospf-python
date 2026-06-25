"""Gantt scheduling better task maximization."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BetterTaskMaximization:
    """Gantt scheduling better task maximization."""

    name: str = "better task maximization"

    def build_objective_terms(self, model, tasks):
        """Build solver objective terms."""
        return ()

    def compute_value(self, schedule):
        """Compute objective value."""
        return 0.0
