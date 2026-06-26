"""Gantt scheduling task compilation aliases."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


@dataclass(frozen=True)
class ConstraintEntry:
    """Constraint entry for task compilation."""

    name: str
    coefficients: Union[
        dict[str, float],
        tuple[tuple[str, float], ...],
    ] = field(default_factory=dict)
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
    # 支持关键字别名 / Support keyword aliases
    lower_bound: float = 0.0
    upper_bound: float = float("inf")
    is_integer: bool = False
    coefficient: float = 0.0


@dataclass(frozen=True)
class TaskCompilationAliases:
    """Gantt scheduling task compilation aliases."""

    name: str = "task_compilation_aliases"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
