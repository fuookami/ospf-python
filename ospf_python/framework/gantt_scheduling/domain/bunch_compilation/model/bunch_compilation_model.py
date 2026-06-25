"""Gantt scheduling bunch compilation model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BunchCompilationModel:
    """Gantt scheduling bunch compilation model."""

    name: str = "bunch_compilation_model"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
