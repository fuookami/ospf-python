"""Gantt scheduling gantt shadow price map."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GanttShadowPriceMap:
    """Gantt scheduling gantt shadow price map."""

    name: str = "gantt shadow price map"

    @property
    def is_valid(self):
        """Check if model is valid."""
        return bool(self.name)
