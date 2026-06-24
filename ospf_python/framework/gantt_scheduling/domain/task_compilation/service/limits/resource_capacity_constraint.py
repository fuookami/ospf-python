"""Gantt scheduling resource_capacity_constraint.

Provides resource_capacity_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceCapacityConstraint:
    """Gantt scheduling ResourceCapacityConstraint."""

    pass
