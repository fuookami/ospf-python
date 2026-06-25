"""Gantt scheduling capacity scheduling solver value adapter."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapacitySchedulingSolverValueAdapter:
    """Gantt scheduling capacity scheduling solver value adapter."""

    name: str = "capacity_scheduling_solver_value_adapter"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
