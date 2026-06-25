"""Gantt scheduling bunch problem."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BunchProblem:
    """Gantt scheduling bunch problem."""

    name: str = "bunch problem"

    @property
    def is_valid(self):
        """Check if model is valid."""
        return bool(self.name)
