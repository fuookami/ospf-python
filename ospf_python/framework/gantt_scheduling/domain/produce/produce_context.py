"""Gantt scheduling produce context."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProduceContext:
    """Gantt scheduling produce context."""

    name: str = "produce context"

    def analyze(self, data: object) -> dict[str, str]:
        """Analyze scheduling data."""
        return {"status": "ok"}
