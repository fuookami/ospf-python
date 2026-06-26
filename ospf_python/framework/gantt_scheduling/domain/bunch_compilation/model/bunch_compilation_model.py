"""Gantt scheduling bunch compilation model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BunchCompilationModel:
    """Gantt scheduling bunch compilation model."""

    name: str = "bunch_compilation_model"
    aggregation: Any = None

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)

    def with_config(self, config: Any) -> BunchCompilationModel:
        """创建不同配置的模型副本。/ Create copy with config."""
        return BunchCompilationModel(
            name=self.name,
            aggregation=self.aggregation,
        )
