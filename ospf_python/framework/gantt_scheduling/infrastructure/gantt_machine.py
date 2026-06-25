"""Gantt scheduling gantt machine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GanttMachine:
    """Gantt scheduling gantt machine."""

    name: str = "gantt machine"

    @property
    def is_valid(self):
        """Check if model is valid."""
        return bool(self.name)
