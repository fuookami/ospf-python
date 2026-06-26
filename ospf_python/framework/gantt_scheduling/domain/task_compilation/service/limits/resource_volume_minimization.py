"""Gantt scheduling resource volume minimization."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceVolumeMinimization:
    """Gantt scheduling resource volume minimization."""

    name: str = "resource volume minimization"

    def build_objective_terms(self, model: object, tasks: object) -> tuple[()]:
        """Build solver objective terms."""
        return ()

    def compute_value(self, schedule: object) -> float:
        """Compute objective value."""
        return 0.0
