"""Gantt scheduling produce aliases."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProduceAliases:
    """Gantt scheduling produce aliases."""

    name: str = "produce_aliases"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
