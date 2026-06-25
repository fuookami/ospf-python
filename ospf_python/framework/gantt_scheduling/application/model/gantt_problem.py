"""Gantt scheduling gantt problem."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GanttProblem:
    """Gantt scheduling gantt problem."""

    name: str = "gantt problem"

    @property
    def is_valid(self):
        """Check if model is valid."""
        return bool(self.name)
