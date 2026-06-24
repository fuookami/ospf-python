"""Gantt scheduling produce_context.

Provides produce_context functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProduceContext:
    """Gantt scheduling ProduceContext."""

    pass
