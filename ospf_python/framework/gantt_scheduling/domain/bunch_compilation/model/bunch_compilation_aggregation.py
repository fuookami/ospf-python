"""Gantt scheduling bunch compilation aggregation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BunchCompilationAggregation:
    """Gantt scheduling bunch compilation aggregation."""

    name: str = "bunch_compilation_aggregation"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
