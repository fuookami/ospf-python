"""Gantt scheduling produce_batch_capacity_constraint.

Provides produce_batch_capacity_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProduceBatchCapacityConstraint:
    """Gantt scheduling ProduceBatchCapacityConstraint."""

    pass
