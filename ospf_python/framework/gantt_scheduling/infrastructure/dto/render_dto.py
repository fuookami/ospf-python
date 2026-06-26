"""Gantt scheduling render dto."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RenderDto:
    """Gantt scheduling render dto."""

    name: str = "render dto"

    @property
    def is_valid(self) -> bool:
        """Check if model is valid."""
        return bool(self.name)
