"""Gantt scheduling capacity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Capacity:
    """Gantt scheduling capacity."""

    name: str = "capacity"
    resource_key: str = ""
    window_start: float = 0.0
    window_end: float = 0.0
    max_capacity: float = 0.0
    load_amount: float = 0.0

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
