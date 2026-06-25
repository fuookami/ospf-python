"""Gantt scheduling bunch generation program candidate adapters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BunchGenerationProgramCandidateAdapters:
    """Gantt scheduling bunch generation program candidate adapters."""

    name: str = "bunch_generation_program_candidate_adapters"

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)
