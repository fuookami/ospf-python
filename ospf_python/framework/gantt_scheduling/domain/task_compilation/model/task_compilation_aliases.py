"""Gantt scheduling task compilation aliases."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConstraintEntry:
    """Constraint entry for task compilation."""

    name: str
    coefficients: dict[str, float] = field(default_factory=dict)
    sense: str = "<="
    rhs: float = 0.0


@dataclass(frozen=True)
class VariableEntry:
    """Variable entry for task compilation."""

    name: str
    lb: float = 0.0
    ub: float = float("inf")
    obj: float = 0.0
    vtype: str = "C"


@dataclass(frozen=True)
class TaskCompilationAliases:
    """Gantt scheduling task compilation aliases."""

    name: str = "task_compilation_aliases"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
