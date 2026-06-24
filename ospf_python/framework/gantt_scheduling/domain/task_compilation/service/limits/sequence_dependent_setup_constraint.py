"""Gantt scheduling sequence_dependent_setup_constraint.

Provides sequence_dependent_setup_constraint functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SequenceDependentSetupConstraint:
    """Gantt scheduling SequenceDependentSetupConstraint."""

    pass
