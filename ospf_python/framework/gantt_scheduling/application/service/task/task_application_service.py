"""Gantt scheduling task application service."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskApplicationService:
    """Gantt scheduling task application service."""

    name: str = "task application service"

    def analyze(self, data):
        """Analyze scheduling data."""
        return {"status": "ok"}
