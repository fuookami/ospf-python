"""Gantt scheduling produce aggregation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProduceAggregation:
    """Gantt scheduling produce aggregation."""

    name: str = "produce_aggregation"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
