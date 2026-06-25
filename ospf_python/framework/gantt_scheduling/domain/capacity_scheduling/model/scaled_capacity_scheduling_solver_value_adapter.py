"""Gantt scheduling scaled capacity scheduling solver value adapter."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScaledCapacitySchedulingSolverValueAdapter:
    """Gantt scheduling scaled capacity scheduling solver value adapter."""

    name: str = "scaled_capacity_scheduling_solver_value_adapter"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
