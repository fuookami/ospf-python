"""Gantt scheduling resource_context.

Provides resource_context functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceContext:
    """Gantt scheduling ResourceContext."""

    pass
