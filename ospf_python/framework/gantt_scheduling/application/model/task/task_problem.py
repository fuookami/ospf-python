"""Gantt scheduling task problem."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskProblem:
    """Gantt scheduling task problem."""

    name: str = "task problem"

    @property
    def is_valid(self):
        """Check if model is valid."""
        return bool(self.name)
