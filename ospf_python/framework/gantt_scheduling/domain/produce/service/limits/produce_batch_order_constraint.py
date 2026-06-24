"""Gantt scheduling produce_batch_order_constraint.

Provides produce_batch_order_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProduceBatchOrderConstraint:
    """Gantt scheduling ProduceBatchOrderConstraint."""

    pass
