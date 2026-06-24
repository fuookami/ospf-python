"""Gantt scheduling bunch_demand_constraint.

Provides bunch_demand_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BunchDemandConstraint:
    """Gantt scheduling BunchDemandConstraint."""

    pass
