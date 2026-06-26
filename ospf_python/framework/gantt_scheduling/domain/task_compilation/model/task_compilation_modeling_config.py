"""Gantt scheduling task compilation modeling config."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskCompilationModelingConfig:
    """Gantt scheduling task compilation modeling config."""

    name: str = "task_compilation_modeling_config"
    default_objective_weight: float = 1.0
    precision: float = 1e-6

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
