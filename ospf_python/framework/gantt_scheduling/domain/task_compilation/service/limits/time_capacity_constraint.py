"""Gantt scheduling time_capacity_constraint.

Provides time_capacity_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeCapacityConstraint:
    """Gantt scheduling TimeCapacityConstraint."""

    pass
