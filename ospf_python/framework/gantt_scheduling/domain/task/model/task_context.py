"""Gantt scheduling task_context.

Provides task_context functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskContext:
    """Gantt scheduling TaskContext."""

    pass
