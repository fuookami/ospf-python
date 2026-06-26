"""Gantt scheduling gantt container."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GanttContainer:
    """Gantt scheduling gantt container."""

    name: str = "gantt container"

    @property
    def is_valid(self) -> bool:
        """Check if model is valid."""
        return bool(self.name)
