"""Gantt scheduling task solution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskSolution:
    """Gantt scheduling task solution."""

    name: str = "task solution"

    @property
    def is_valid(self):
        """Check if model is valid."""
        return bool(self.name)
