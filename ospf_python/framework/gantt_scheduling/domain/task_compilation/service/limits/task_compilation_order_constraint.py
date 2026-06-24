"""Gantt scheduling task_compilation_order_constraint.

Provides task_compilation_order_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskCompilationOrderConstraint:
    """Gantt scheduling TaskCompilationOrderConstraint."""

    pass
