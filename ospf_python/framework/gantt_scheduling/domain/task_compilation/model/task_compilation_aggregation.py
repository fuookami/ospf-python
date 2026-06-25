"""Gantt scheduling task compilation aggregation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskCompilationAggregation:
    """Gantt scheduling task compilation aggregation."""

    name: str = "task_compilation_aggregation"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
