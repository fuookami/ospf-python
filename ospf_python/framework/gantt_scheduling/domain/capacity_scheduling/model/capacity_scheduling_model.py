"""Gantt scheduling capacity scheduling model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapacitySchedulingModel:
    """Gantt scheduling capacity scheduling model."""

    name: str = "capacity_scheduling_model"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
