"""Gantt scheduling scaled produce solver value adapter."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScaledProduceSolverValueAdapter:
    """Gantt scheduling scaled produce solver value adapter."""

    name: str = "scaled_produce_solver_value_adapter"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
