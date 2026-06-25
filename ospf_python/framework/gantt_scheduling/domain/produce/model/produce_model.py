"""Gantt scheduling produce model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProduceModel:
    """Gantt scheduling produce model."""

    name: str = "produce_model"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
