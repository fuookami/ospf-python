"""Gantt scheduling batch_capacity_constraint.

Provides batch_capacity_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BatchCapacityConstraint:
    """Gantt scheduling BatchCapacityConstraint."""

    pass
