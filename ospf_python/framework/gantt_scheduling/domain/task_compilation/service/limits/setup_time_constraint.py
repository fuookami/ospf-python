"""Gantt scheduling setup_time_constraint.

Provides setup_time_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SetupTimeConstraint:
    """Gantt scheduling SetupTimeConstraint."""

    pass
