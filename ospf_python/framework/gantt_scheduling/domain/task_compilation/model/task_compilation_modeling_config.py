"""Gantt scheduling task compilation modeling config."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskCompilationModelingConfig:
    """Gantt scheduling task compilation modeling config."""

    name: str = "task_compilation_modeling_config"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
