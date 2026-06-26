"""货舱定义 / Stowage compartment definition.

定义飞机货舱的属性和容量限制。
Defines aircraft compartment properties and capacity limits.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StowageCompartment:
    """货舱 / Stowage compartment.

    描述飞机上的货舱，包括甲板位置、最大重量和最大容积。
    Describes an aircraft compartment, including deck location,
    maximum weight, and maximum volume.

    Attributes:
        comp_id: 舱室标识 / Compartment identifier.
        deck: 甲板位置（UPPER/LOWER）/
            Deck location (UPPER/LOWER).
        max_weight: 最大承载重量（千克）/
            Maximum weight capacity (kg).
        max_volume: 最大承载容积（立方米）/
            Maximum volume capacity (cubic meters).
    """

    comp_id: str = ""
    """舱室标识 / Compartment identifier."""

    deck: str = "LOWER"
    """甲板位置 / Deck location."""

    max_weight: float = 0.0
    """最大承载重量（千克）/ Maximum weight capacity (kg)."""

    max_volume: float = 0.0
    """最大承载容积（立方米）/ Maximum volume capacity (cubic meters)."""

    @staticmethod
    def create(
        *,
        comp_id: str,
        deck: str = "LOWER",
        max_weight: float,
        max_volume: float,
    ) -> StowageCompartment:
        """创建货舱。

        Create compartment.

        Args:
            comp_id: 舱室标识。/ Compartment identifier.
            deck: 甲板位置，默认 LOWER。/
                Deck location, default LOWER.
            max_weight: 最大承载重量（千克）。/
                Maximum weight capacity (kg).
            max_volume: 最大承载容积（立方米）。/
                Maximum volume capacity (cubic meters).

        Returns:
            货舱实例。/ Compartment instance.
        """
        return StowageCompartment(
            comp_id=comp_id,
            deck=deck,
            max_weight=max_weight,
            max_volume=max_volume,
        )

    @property
    def is_upper_deck(self) -> bool:
        """是否为上层甲板。

        Whether this is an upper deck compartment.

        Returns:
            甲板位置为 UPPER 时返回 True。
            True if deck location is UPPER.
        """
        return self.deck == "UPPER"

    @property
    def is_lower_deck(self) -> bool:
        """是否为下层甲板。

        Whether this is a lower deck compartment.

        Returns:
            甲板位置为 LOWER 时返回 True。
            True if deck location is LOWER.
        """
        return self.deck == "LOWER"

    def weight_utilization(
        self,
        current_weight: float,
    ) -> float:
        """计算重量利用率。

        Calculate weight utilization ratio.

        Args:
            current_weight: 当前装载重量（千克）。/
                Current loaded weight (kg).

        Returns:
            利用率（0.0-1.0），最大重量为零时返回 0.0。
            Utilization ratio (0.0-1.0), or 0.0 if max weight is zero.
        """
        if self.max_weight <= 0.0:
            return 0.0
        return min(1.0, current_weight / self.max_weight)

    def volume_utilization(
        self,
        current_volume: float,
    ) -> float:
        """计算容积利用率。

        Calculate volume utilization ratio.

        Args:
            current_volume: 当前装载容积（立方米）。/
                Current loaded volume (cubic meters).

        Returns:
            利用率（0.0-1.0），最大容积为零时返回 0.0。
            Utilization ratio (0.0-1.0), or 0.0 if max volume is zero.
        """
        if self.max_volume <= 0.0:
            return 0.0
        return min(1.0, current_volume / self.max_volume)

    def remaining_weight(
        self,
        current_weight: float,
    ) -> float:
        """计算剩余重量容量。

        Calculate remaining weight capacity.

        Args:
            current_weight: 当前装载重量（千克）。/
                Current loaded weight (kg).

        Returns:
            剩余重量（千克），最小为 0.0。
            Remaining weight (kg), minimum 0.0.
        """
        return max(0.0, self.max_weight - current_weight)

    def remaining_volume(
        self,
        current_volume: float,
    ) -> float:
        """计算剩余容积。

        Calculate remaining volume capacity.

        Args:
            current_volume: 当前装载容积（立方米）。/
                Current loaded volume (cubic meters).

        Returns:
            剩余容积（立方米），最小为 0.0。
            Remaining volume (cubic meters), minimum 0.0.
        """
        return max(0.0, self.max_volume - current_volume)
