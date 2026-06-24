"""Gantt scheduling task_demand_constraint.

Provides task_demand_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskDemandConstraint:
    """Gantt scheduling TaskDemandConstraint."""

    pass
