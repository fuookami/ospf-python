"""Gantt scheduling bunch_generation_context.

Provides bunch_generation_context functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BunchGenerationContext:
    """Gantt scheduling BunchGenerationContext."""

    pass
