"""Gantt scheduling capacity scheduling modeling config."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapacitySchedulingModelingConfig:
    """Gantt scheduling capacity scheduling modeling config."""

    name: str = "capacity_scheduling_modeling_config"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
