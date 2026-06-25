"""Gantt scheduling capacity scheduling aggregation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapacitySchedulingAggregation:
    """Gantt scheduling capacity scheduling aggregation."""

    name: str = "capacity_scheduling_aggregation"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
