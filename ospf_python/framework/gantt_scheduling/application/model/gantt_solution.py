"""Gantt scheduling gantt solution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GanttSolution:
    """Gantt scheduling gantt solution."""

    name: str = "gantt solution"

    @property
    def is_valid(self):
        """Check if model is valid."""
        return bool(self.name)
