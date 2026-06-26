"""Gantt scheduling aggregation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Aggregation:
    """Gantt scheduling aggregation."""

    name: str = "aggregation"

    def add(self, item: object) -> Aggregation:
        """Add item to aggregation."""
        return self

    def remove(self, key: str) -> Aggregation:
        """Remove item from aggregation."""
        return self
