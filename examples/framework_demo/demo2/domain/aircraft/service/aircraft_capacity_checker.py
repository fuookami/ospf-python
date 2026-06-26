"""航空器容量检查器 / Aircraft capacity checker.

检查航空器货舱的体积和重量容量。
Checks aircraft cargo hold volume and weight capacity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.aircraft.model.aircraft import Aircraft
    from examples.framework_demo.demo2.domain.aircraft.model.deck import Deck


@dataclass(frozen=True)
class CapacityReport:
    """容量报告 / Capacity report.

    Attributes:
        total_volume: 总可用体积 (m^3) / Total available volume (m^3).
        used_volume: 已用体积 (m^3) / Used volume (m^3).
        remaining_volume: 剩余体积 (m^3) / Remaining volume (m^3).
        volume_utilization: 体积利用率 / Volume utilization ratio.
        total_weight_capacity: 总重量容量 (kg) / Total weight capacity (kg).
        used_weight: 已用重量 (kg) / Used weight (kg).
        remaining_weight: 剩余重量 (kg) / Remaining weight (kg).
        weight_utilization: 重量利用率 / Weight utilization ratio.
    """

    total_volume: float
    """总可用体积 (m^3) / Total available volume (m^3)."""

    used_volume: float
    """已用体积 (m^3) / Used volume (m^3)."""

    remaining_volume: float
    """剩余体积 (m^3) / Remaining volume (m^3)."""

    volume_utilization: float
    """体积利用率 / Volume utilization ratio."""

    total_weight_capacity: float
    """总重量容量 (kg) / Total weight capacity (kg)."""

    used_weight: float
    """已用重量 (kg) / Used weight (kg)."""

    remaining_weight: float
    """剩余重量 (kg) / Remaining weight (kg)."""

    weight_utilization: float
    """重量利用率 / Weight utilization ratio."""


@dataclass(frozen=True)
class DeckCapacity:
    """甲板容量 / Deck capacity.

    Attributes:
        deck_id: 甲板标识 / Deck identifier.
        max_volume: 最大体积 (m^3) / Max volume (m^3).
        used_volume: 已用体积 (m^3) / Used volume (m^3).
        max_load: 最大载荷 (kg) / Max load (kg).
        used_load: 已用载荷 (kg) / Used load (kg).
    """

    deck_id: str
    """甲板标识 / Deck identifier."""

    max_volume: float
    """最大体积 (m^3) / Max volume (m^3)."""

    used_volume: float
    """已用体积 (m^3) / Used volume (m^3)."""

    max_load: float
    """最大载荷 (kg) / Max load (kg)."""

    used_load: float
    """已用载荷 (kg) / Used load (kg)."""

    @property
    def remaining_volume(self) -> float:
        """剩余体积 / Remaining volume.

        Returns:
            max(0, max_volume - used_volume).
        """
        return max(0.0, self.max_volume - self.used_volume)

    @property
    def remaining_load(self) -> float:
        """剩余载荷 / Remaining load.

        Returns:
            max(0, max_load - used_load).
        """
        return max(0.0, self.max_load - self.used_load)

    @property
    def is_volume_full(self) -> bool:
        """体积是否已满 / Whether volume is full.

        Returns:
            已用体积不小于最大体积时为 True /
            True when used volume >= max volume.
        """
        return self.used_volume >= self.max_volume

    @property
    def is_load_full(self) -> bool:
        """载荷是否已满 / Whether load is full.

        Returns:
            已用载荷不小于最大载荷时为 True /
            True when used load >= max load.
        """
        return self.used_load >= self.max_load


class AircraftCapacityChecker:
    """航空器容量检查器 / Aircraft capacity checker.

    检查货舱体积和重量容量，判断是否可容纳新货物。
    Checks cargo hold volume and weight capacity to determine
    whether new cargo can be accommodated.
    """

    def check_cargo_fit(
        self,
        *,
        aircraft: Aircraft,
        cargo_volume: float,
        cargo_weight: float,
        current_used_volume: float,
        current_used_weight: float,
    ) -> Result[CapacityReport, str, Err[str]]:
        """检查货物是否可装入 / Check if cargo fits.

        Args:
            aircraft: 航空器 / Aircraft.
            cargo_volume: 待装货物体积 (m^3) / Cargo volume to load (m^3).
            cargo_weight: 待装货物重量 (kg) / Cargo weight to load (kg).
            current_used_volume: 当前已用体积 (m^3) / Current used volume (m^3).
            current_used_weight: 当前已用重量 (kg) / Current used weight (kg).

        Returns:
            容量报告 / Capacity report.
        """
        total_volume = aircraft.cargo_hold_volume
        total_weight = aircraft.max_zero_fuel_weight

        new_used_volume = current_used_volume + cargo_volume
        new_used_weight = current_used_weight + cargo_weight

        remaining_volume = max(0.0, total_volume - new_used_volume)
        remaining_weight = max(0.0, total_weight - new_used_weight)

        volume_util = new_used_volume / total_volume if total_volume > 0 else 0.0
        weight_util = new_used_weight / total_weight if total_weight > 0 else 0.0

        report = CapacityReport(
            total_volume=total_volume,
            used_volume=new_used_volume,
            remaining_volume=remaining_volume,
            volume_utilization=volume_util,
            total_weight_capacity=total_weight,
            used_weight=new_used_weight,
            remaining_weight=remaining_weight,
            weight_utilization=weight_util,
        )

        if new_used_volume > total_volume:
            return Failed(
                Err(
                    _code=ErrorCode.RESOURCE_EXHAUSTED,
                    _message=(
                        f"Volume overflow: need {new_used_volume:.2f} m^3 "
                        f"but capacity is {total_volume:.2f} m^3"
                    ),
                )
            )

        if new_used_weight > total_weight:
            return Failed(
                Err(
                    _code=ErrorCode.RESOURCE_EXHAUSTED,
                    _message=(
                        f"Weight overflow: need {new_used_weight:.1f} kg "
                        f"but MZFW is {total_weight:.1f} kg"
                    ),
                )
            )

        return Ok(report)

    def check_deck_capacity(
        self,
        *,
        deck: Deck,
        cargo_volume: float,
        cargo_weight: float,
        current_used_volume: float,
        current_used_load: float,
    ) -> Result[DeckCapacity, str, Err[str]]:
        """检查甲板容量 / Check deck capacity.

        Args:
            deck: 甲板 / Deck.
            cargo_volume: 待装货物体积 (m^3) / Cargo volume (m^3).
            cargo_weight: 待装货物重量 (kg) / Cargo weight (kg).
            current_used_volume: 当前已用体积 (m^3) / Current used volume (m^3).
            current_used_load: 当前已用载荷 (kg) / Current used load (kg).

        Returns:
            甲板容量报告 / Deck capacity report.
        """
        new_used_volume = current_used_volume + cargo_volume
        new_used_load = current_used_load + cargo_weight

        capacity = DeckCapacity(
            deck_id=deck.deck_id,
            max_volume=deck.volume,
            used_volume=new_used_volume,
            max_load=deck.max_load,
            used_load=new_used_load,
        )

        if new_used_volume > deck.volume:
            return Failed(
                Err(
                    _code=ErrorCode.RESOURCE_EXHAUSTED,
                    _message=(
                        f"Deck {deck.deck_id} volume overflow: "
                        f"need {new_used_volume:.2f} m^3 "
                        f"but capacity is {deck.volume:.2f} m^3"
                    ),
                )
            )

        if new_used_load > deck.max_load:
            return Failed(
                Err(
                    _code=ErrorCode.RESOURCE_EXHAUSTED,
                    _message=(
                        f"Deck {deck.deck_id} load overflow: "
                        f"need {new_used_load:.1f} kg "
                        f"but limit is {deck.max_load:.1f} kg"
                    ),
                )
            )

        return Ok(capacity)

    def estimate_utilization(
        self,
        *,
        aircraft: Aircraft,
        total_cargo_volume: float,
        total_cargo_weight: float,
    ) -> tuple[float, float]:
        """估算利用率 / Estimate utilization.

        Args:
            aircraft: 航空器 / Aircraft.
            total_cargo_volume: 总货物体积 (m^3) / Total cargo volume (m^3).
            total_cargo_weight: 总货物重量 (kg) / Total cargo weight (kg).

        Returns:
            (体积利用率, 重量利用率) / (volume utilization, weight utilization).
        """
        vol_util = (
            total_cargo_volume / aircraft.cargo_hold_volume
            if aircraft.cargo_hold_volume > 0
            else 0.0
        )
        wt_util = (
            total_cargo_weight / aircraft.max_zero_fuel_weight
            if aircraft.max_zero_fuel_weight > 0
            else 0.0
        )
        return (vol_util, wt_util)
