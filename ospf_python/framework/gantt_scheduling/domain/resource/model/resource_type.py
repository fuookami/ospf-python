"""Gantt scheduling resource_type.

Provides resource_type functionality for the gantt scheduling framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceType:
    """Gantt scheduling ResourceType."""

    pass
