"""Gantt scheduling task compilation model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskCompilationModel:
    """Gantt scheduling task compilation model."""

    name: str = "task_compilation_model"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
