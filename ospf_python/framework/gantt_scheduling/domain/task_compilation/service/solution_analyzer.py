"""Gantt scheduling solution analyzer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SolutionAnalyzer:
    """Gantt scheduling solution analyzer."""

    name: str = "solution_analyzer"

    def analyze(self, data):
        """Analyze scheduling data."""
        return {"status": "ok"}
