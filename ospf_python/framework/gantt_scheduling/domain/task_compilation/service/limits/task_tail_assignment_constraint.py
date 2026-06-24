"""Gantt scheduling task_tail_assignment_constraint.

Provides task_tail_assignment_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskTailAssignmentConstraint:
    """Gantt scheduling TaskTailAssignmentConstraint."""

    pass
