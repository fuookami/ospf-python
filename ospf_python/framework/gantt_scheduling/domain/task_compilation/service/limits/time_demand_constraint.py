"""Gantt scheduling time_demand_constraint.

Provides time_demand_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeDemandConstraint:
    """Gantt scheduling TimeDemandConstraint."""

    pass
