"""Gantt scheduling capacity scheduling model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CapacitySchedulingModel:
    """Gantt scheduling capacity scheduling model."""

    name: str = "capacity_scheduling_model"
    aggregation: Any = None

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)

    def with_config(
        self,
        config: Any,
    ) -> CapacitySchedulingModel:
        """创建不同配置的模型副本。/ Create copy with config."""
        return CapacitySchedulingModel(
            name=self.name,
            aggregation=self.aggregation,
        )
