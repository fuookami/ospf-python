"""Gantt scheduling bunch compilation solver value adapter."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BunchCompilationSolverValueAdapter:
    """Gantt scheduling bunch compilation solver value adapter."""

    name: str = "bunch_compilation_solver_value_adapter"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
