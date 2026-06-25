"""Gantt scheduling time volume minimization."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeVolumeMinimization:
    """Gantt scheduling time volume minimization."""

    name: str = "time volume minimization"

    def build_objective_terms(self, model, tasks):
        """Build solver objective terms."""
        return ()

    def compute_value(self, schedule):
        """Compute objective value."""
        return 0.0
