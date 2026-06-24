"""Gantt scheduling task_type.

Provides task_type functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskType:
    """Gantt scheduling TaskType."""

    pass
