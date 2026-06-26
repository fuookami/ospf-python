"""Gantt scheduling gantt material."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GanttMaterial:
    """Gantt scheduling gantt material."""

    name: str = "gantt material"

    @property
    def is_valid(self) -> bool:
        """Check if model is valid."""
        return bool(self.name)
