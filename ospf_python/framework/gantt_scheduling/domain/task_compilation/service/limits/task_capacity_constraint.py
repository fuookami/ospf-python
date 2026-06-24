"""Gantt scheduling task_capacity_constraint.

Provides task_capacity_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskCapacityConstraint:
    """Gantt scheduling TaskCapacityConstraint."""

    pass
