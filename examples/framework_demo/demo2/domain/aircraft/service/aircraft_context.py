"""航空器上下文 / Aircraft context.

封装航空器运行时状态，提供便捷的查询方法。
Encapsulates aircraft runtime state with convenient
query methods.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from examples.framework_demo.demo2.domain.aircraft.model.flight_phase import (
    FlightPhase,
)

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.aircraft.model.aircraft import Aircraft
    from examples.framework_demo.demo2.domain.aircraft.model.aircraft_aggregation import (
        AircraftAggregation,
    )
    from examples.framework_demo.demo2.domain.aircraft.model.deck import Deck


@dataclass(frozen=True)
class AircraftContext:
    """航空器上下文 / Aircraft context.

    持有当前航空器的运行时状态，包括当前注册号、
    当前飞行阶段和燃油剩余量，并提供状态查询方法。
    Holds the current aircraft runtime state including
    registration, flight phase, and remaining fuel,
    with state query methods.

    Attributes:
        aircraft_aggregation: 航空器聚合 / Aircraft aggregation.
        current_registration: 当前注册号 / Current registration.
        current_phase: 当前飞行阶段 / Current flight phase.
        remaining_fuel_weight: 剩余燃油重量 (kg) / Remaining fuel weight (kg).
        current_payload_weight: 当前载荷重量 (kg) / Current payload weight (kg).
    """

    aircraft_aggregation: AircraftAggregation
    """航空器聚合 / Aircraft aggregation."""

    current_registration: str
    """当前注册号 / Current registration."""

    current_phase: FlightPhase
    """当前飞行阶段 / Current flight phase."""

    remaining_fuel_weight: float
    """剩余燃油重量 (kg) / Remaining fuel weight (kg)."""

    current_payload_weight: float
    """当前载荷重量 (kg) / Current payload weight (kg)."""

    @staticmethod
    def create(
        *,
        aircraft_aggregation: AircraftAggregation,
        current_registration: str,
        current_phase: FlightPhase = FlightPhase.CRUISE,
        remaining_fuel_weight: float = 0.0,
        current_payload_weight: float = 0.0,
    ) -> AircraftContext:
        """创建航空器上下文 / Create aircraft context.

        Args:
            aircraft_aggregation: 航空器聚合 / Aircraft aggregation.
            current_registration: 当前注册号 / Current registration.
            current_phase: 当前飞行阶段，默认巡航 / Current phase, default cruise.
            remaining_fuel_weight: 剩余燃油重量 / Remaining fuel weight.
            current_payload_weight: 当前载荷重量 / Current payload weight.

        Returns:
            航空器上下文实例 / Aircraft context instance.
        """
        return AircraftContext(
            aircraft_aggregation=aircraft_aggregation,
            current_registration=current_registration,
            current_phase=current_phase,
            remaining_fuel_weight=remaining_fuel_weight,
            current_payload_weight=current_payload_weight,
        )

    @property
    def current_aircraft(self) -> Aircraft | None:
        """获取当前航空器 / Get current aircraft.

        Returns:
            当前注册号对应的航空器或 None /
            Aircraft for current registration or None.
        """
        return self.aircraft_aggregation.by_registration(
            self.current_registration,
        )

    @property
    def current_total_weight(self) -> float:
        """当前总重量 / Current total weight.

        结构重量 + 载荷 + 燃油。
        Structural weight + payload + fuel.

        Returns:
            当前总重量 (kg) / Current total weight (kg).
        """
        aircraft = self.current_aircraft
        if aircraft is None:
            return 0.0
        base_weight = aircraft.max_zero_fuel_weight
        return base_weight + self.remaining_fuel_weight

    @property
    def available_payload_capacity(self) -> float:
        """剩余可用载荷能力 / Remaining payload capacity.

        基于当前飞行阶段和最大零油重量计算。
        Based on current phase and max zero fuel weight.

        Returns:
            剩余可用载荷 (kg) / Remaining payload capacity (kg).
        """
        aircraft = self.current_aircraft
        if aircraft is None:
            return 0.0
        max_payload = (
            aircraft.max_zero_fuel_weight * self.current_phase.weight_limit_factor
        )
        return max(0.0, max_payload - self.current_payload_weight)

    def with_phase(self, phase: FlightPhase) -> AircraftContext:
        """切换飞行阶段（返回新上下文）/ Switch flight phase (returns new context).

        Args:
            phase: 新飞行阶段 / New flight phase.

        Returns:
            新上下文实例 / New context instance.
        """
        return AircraftContext(
            aircraft_aggregation=self.aircraft_aggregation,
            current_registration=self.current_registration,
            current_phase=phase,
            remaining_fuel_weight=self.remaining_fuel_weight,
            current_payload_weight=self.current_payload_weight,
        )

    def with_fuel(self, remaining_fuel_weight: float) -> AircraftContext:
        """更新燃油量（返回新上下文）/ Update fuel (returns new context).

        Args:
            remaining_fuel_weight: 新剩余燃油重量 / New remaining fuel weight.

        Returns:
            新上下文实例 / New context instance.
        """
        return AircraftContext(
            aircraft_aggregation=self.aircraft_aggregation,
            current_registration=self.current_registration,
            current_phase=self.current_phase,
            remaining_fuel_weight=remaining_fuel_weight,
            current_payload_weight=self.current_payload_weight,
        )

    def with_payload(self, current_payload_weight: float) -> AircraftContext:
        """更新载荷重量（返回新上下文）/ Update payload (returns new context).

        Args:
            current_payload_weight: 新载荷重量 / New payload weight.

        Returns:
            新上下文实例 / New context instance.
        """
        return AircraftContext(
            aircraft_aggregation=self.aircraft_aggregation,
            current_registration=self.current_registration,
            current_phase=self.current_phase,
            remaining_fuel_weight=self.remaining_fuel_weight,
            current_payload_weight=current_payload_weight,
        )

    def lookup_deck(self, deck_id: str) -> Deck | None:
        """按标识查找当前航空器的甲板 / Lookup deck on current aircraft.

        通过遍历聚合中所有航空器查找（简化实现）。
        Searches by iterating aggregation (simplified).

        Args:
            deck_id: 甲板标识 / Deck identifier.

        Returns:
            匹配的甲板或 None / Matching deck or None.
        """
        # NOTE: In a real system this would load from AircraftModel.
        # Here we return None as deck data is not part of Aircraft entity.
        return None
