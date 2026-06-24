"""交换协议 / Swap protocol."""

from __future__ import annotations

from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class Swappable(Protocol):
    """可交换协议 / Swappable protocol."""

    def swap(self, other: Self) -> tuple[Self, Self]:
        """交换值 / Swap values."""
