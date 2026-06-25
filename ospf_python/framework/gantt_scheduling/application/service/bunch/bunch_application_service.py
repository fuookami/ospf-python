"""Gantt scheduling bunch application service."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BunchApplicationService:
    """Gantt scheduling bunch application service."""

    name: str = "bunch application service"

    def analyze(self, data):
        """Analyze scheduling data."""
        return {"status": "ok"}
