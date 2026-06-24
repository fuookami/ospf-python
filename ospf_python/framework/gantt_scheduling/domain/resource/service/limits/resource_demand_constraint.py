"""Gantt scheduling resource_demand_constraint.

Provides resource_demand_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceDemandConstraint:
    """Gantt scheduling ResourceDemandConstraint."""

    pass
