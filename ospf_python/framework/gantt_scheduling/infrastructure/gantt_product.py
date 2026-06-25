"""Gantt scheduling gantt product."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GanttProduct:
    """Gantt scheduling gantt product."""

    name: str = "gantt product"

    @property
    def is_valid(self):
        """Check if model is valid."""
        return bool(self.name)
