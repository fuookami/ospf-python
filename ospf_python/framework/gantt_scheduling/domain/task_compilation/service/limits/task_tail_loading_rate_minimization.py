"""Gantt scheduling task tail loading rate minimization."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskTailLoadingRateMinimization:
    """Gantt scheduling task tail loading rate minimization."""

    name: str = "task tail loading rate minimization"

    def build_objective_terms(self, model, tasks):
        """Build solver objective terms."""
        return ()

    def compute_value(self, schedule):
        """Compute objective value."""
        return 0.0
