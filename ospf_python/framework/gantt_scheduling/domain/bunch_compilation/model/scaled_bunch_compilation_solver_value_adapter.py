"""Gantt scheduling scaled bunch compilation solver value adapter."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScaledBunchCompilationSolverValueAdapter:
    """Gantt scheduling scaled bunch compilation solver value adapter."""

    name: str = "scaled_bunch_compilation_solver_value_adapter"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
