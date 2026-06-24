"""Gantt scheduling bunch_capacity_constraint.

Provides bunch_capacity_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BunchCapacityConstraint:
    """Gantt scheduling BunchCapacityConstraint."""

    pass
