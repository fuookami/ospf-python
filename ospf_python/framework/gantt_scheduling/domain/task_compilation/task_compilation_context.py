"""Gantt scheduling task_compilation_context.

Provides task_compilation_context functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskCompilationContext:
    """Gantt scheduling TaskCompilationContext."""

    pass
