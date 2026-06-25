"""Gantt scheduling capacity scheduling aliases."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapacitySchedulingAliases:
    """Gantt scheduling capacity scheduling aliases."""

    name: str = "capacity_scheduling_aliases"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
