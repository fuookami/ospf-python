"""Gantt scheduling bunch generation context."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BunchGenerationContext:
    """Gantt scheduling bunch generation context."""

    name: str = "bunch_generation_context"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
