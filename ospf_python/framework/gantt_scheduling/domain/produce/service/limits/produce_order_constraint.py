"""Gantt scheduling produce_order_constraint.

Provides produce_order_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProduceOrderConstraint:
    """Gantt scheduling ProduceOrderConstraint."""

    pass
