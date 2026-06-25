"""Gantt scheduling resource usage minimization."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceUsageMinimization:
    """Gantt scheduling resource usage minimization."""

    name: str = "resource usage minimization"

    def build_objective_terms(self, model, tasks):
        """Build solver objective terms."""
        return ()

    def compute_value(self, schedule):
        """Compute objective value."""
        return 0.0
