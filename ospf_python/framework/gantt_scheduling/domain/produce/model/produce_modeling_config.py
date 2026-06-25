"""Gantt scheduling produce modeling config."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProduceModelingConfig:
    """Gantt scheduling produce modeling config."""

    name: str = "produce_modeling_config"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
