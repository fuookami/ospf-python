"""Gantt scheduling bunch solution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BunchSolution:
    """Gantt scheduling bunch solution."""

    name: str = "bunch solution"

    @property
    def is_valid(self):
        """Check if model is valid."""
        return bool(self.name)
