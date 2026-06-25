"""Gantt scheduling bunch compilation modeling config."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BunchCompilationModelingConfig:
    """Gantt scheduling bunch compilation modeling config."""

    name: str = "bunch_compilation_modeling_config"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
