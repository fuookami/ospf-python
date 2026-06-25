"""Gantt scheduling bunch compilation aliases."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BunchCompilationAliases:
    """Gantt scheduling bunch compilation aliases."""

    name: str = "bunch_compilation_aliases"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
