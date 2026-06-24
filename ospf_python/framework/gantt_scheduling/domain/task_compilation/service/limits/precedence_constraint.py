"""Gantt scheduling precedence_constraint.

Provides precedence_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrecedenceConstraint:
    """Gantt scheduling PrecedenceConstraint."""

    pass
