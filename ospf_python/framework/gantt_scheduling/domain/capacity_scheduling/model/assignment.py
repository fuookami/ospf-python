"""Gantt scheduling assignment."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Assignment:
    """Gantt scheduling assignment."""

    name: str = "assignment"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)


# Alias for backward compatibility
CapacityAssignment = Assignment
