"""Gantt scheduling capacity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Capacity:
    """Gantt scheduling capacity."""

    name: str = "capacity"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)


# Alias for backward compatibility
SlotCapacity = Capacity
