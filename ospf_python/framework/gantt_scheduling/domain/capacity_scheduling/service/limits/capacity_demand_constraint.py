"""Gantt scheduling capacity_demand_constraint.

Provides capacity_demand_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapacityDemandConstraint:
    """Gantt scheduling CapacityDemandConstraint."""

    pass
