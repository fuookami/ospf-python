"""Gantt scheduling load."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Load:
    """Gantt scheduling load."""

    name: str = "load"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)


# Alias for backward compatibility
BunchLoad = Load
