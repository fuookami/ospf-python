"""Gantt scheduling gantt render adapter."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GanttRenderAdapter:
    """Gantt scheduling gantt render adapter."""

    name: str = "gantt render adapter"

    def convert(self, data):
        """Convert data format."""
        return data

    def restore(self, data):
        """Restore original format."""
        return data
