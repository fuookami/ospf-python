"""Cargo model for shipment management.

货物模型：货物管理 / Cargo model for shipment management.
"""

from __future__ import annotations

from dataclasses import dataclass

HEAVY_THRESHOLD_KG: float = 1000.0
HIGH_PRIORITY_LEVEL: int = 8


@dataclass(frozen=True)
class Cargo:
    """A unit of cargo for transportation scheduling.

    用于运输调度的货物单元。
    """

    cargo_id: str
    weight: float
    volume: float
    priority: int
    destination: str

    @property
    def is_heavy(self) -> bool:
        """Whether the cargo exceeds the heavy threshold.

        货物是否超过重量阈值。
        """
        return self.weight > HEAVY_THRESHOLD_KG

    @property
    def density(self) -> float:
        """Weight per unit volume (kg/m3).

        单位体积重量（kg/m3）。
        """
        if self.volume <= 0.0:
            return 0.0
        return self.weight / self.volume

    @property
    def is_high_priority(self) -> bool:
        """Whether this cargo is high priority.

        此货物是否为高优先级。
        """
        return self.priority >= HIGH_PRIORITY_LEVEL

    @property
    def size_category(self) -> str:
        """Categorize cargo by weight class.

        按重量类别对货物进行分类。
        """
        if self.weight < 100.0:
            return "small"
        if self.weight < 500.0:
            return "medium"
        if self.weight < HEAVY_THRESHOLD_KG:
            return "large"
        return "extra_large"

    def same_destination(self, other: Cargo) -> bool:
        """Check whether two cargos share the same destination.

        检查两个货物是否具有相同目的地。
        """
        return self.destination == other.destination

    def combined_weight(self, other: Cargo) -> float:
        """Calculate the combined weight with another cargo.

        计算与另一个货物的合计重量。
        """
        return self.weight + other.weight

    def combined_volume(self, other: Cargo) -> float:
        """Calculate the combined volume with another cargo.

        计算与另一个货物的合计体积。
        """
        return self.volume + other.volume
