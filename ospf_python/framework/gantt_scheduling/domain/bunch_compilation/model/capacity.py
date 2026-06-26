"""Gantt scheduling capacity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Capacity:
    """Gantt scheduling capacity."""

    name: str = "capacity"
    bunch_key: str = ""
    time_window_start: float = 0.0
    time_window_end: float = 0.0
    max_capacity: float = 0.0
    used_capacity: float = 0.0

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)

    @property
    def remaining_capacity(self) -> float:
        """获取剩余容量。/ Get remaining capacity."""
        return max(0.0, self.max_capacity - self.used_capacity)


# Alias for backward compatibility
BunchCapacity = Capacity
