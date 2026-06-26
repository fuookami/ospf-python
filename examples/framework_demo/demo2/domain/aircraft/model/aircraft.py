"""航空器定义 / Aircraft definition.

扩展 BPP3D 航空货运场景中的航空器定义。
Aircraft definition in extended BPP3D aviation cargo scenarios.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Aircraft:
    """航空器 / Aircraft.

    描述航空货运中使用的航空器及其关键性能参数。
    Describes an aircraft used in air cargo with key
    performance parameters.

    Attributes:
        aircraft_type: 机型代码 / Aircraft type code.
        registration: 注册号 / Registration number.
        max_takeoff_weight: 最大起飞重量 (kg) / Max takeoff weight (kg).
        max_landing_weight: 最大着陆重量 (kg) / Max landing weight (kg).
        max_zero_fuel_weight: 最大零油重量 (kg) / Max zero fuel weight (kg).
        fuel_capacity: 燃油容量 (L) / Fuel capacity (L).
        cargo_hold_volume: 货舱总体积 (m^3) / Total cargo hold volume (m^3).
        deck_count: 甲板层数 / Number of decks.
    """

    aircraft_type: str
    """机型代码 / Aircraft type code."""

    registration: str
    """注册号 / Registration number."""

    max_takeoff_weight: float
    """最大起飞重量 (kg) / Max takeoff weight (kg)."""

    max_landing_weight: float
    """最大着陆重量 (kg) / Max landing weight (kg)."""

    max_zero_fuel_weight: float
    """最大零油重量 (kg) / Max zero fuel weight (kg)."""

    fuel_capacity: float
    """燃油容量 (L) / Fuel capacity (L)."""

    cargo_hold_volume: float
    """货舱总体积 (m^3) / Total cargo hold volume (m^3)."""

    deck_count: int
    """甲板层数 / Number of decks."""

    @staticmethod
    def create(
        *,
        aircraft_type: str,
        registration: str,
        max_takeoff_weight: float,
        max_landing_weight: float,
        max_zero_fuel_weight: float,
        fuel_capacity: float,
        cargo_hold_volume: float,
        deck_count: int = 1,
    ) -> Aircraft:
        """创建航空器实例 / Create aircraft instance.

        Args:
            aircraft_type: 机型代码 / Aircraft type code.
            registration: 注册号 / Registration number.
            max_takeoff_weight: 最大起飞重量 / Max takeoff weight.
            max_landing_weight: 最大着陆重量 / Max landing weight.
            max_zero_fuel_weight: 最大零油重量 / Max zero fuel weight.
            fuel_capacity: 燃油容量 / Fuel capacity.
            cargo_hold_volume: 货舱总体积 / Total cargo hold volume.
            deck_count: 甲板层数，默认 1 / Deck count, default 1.

        Returns:
            航空器实例 / Aircraft instance.
        """
        return Aircraft(
            aircraft_type=aircraft_type,
            registration=registration,
            max_takeoff_weight=max_takeoff_weight,
            max_landing_weight=max_landing_weight,
            max_zero_fuel_weight=max_zero_fuel_weight,
            fuel_capacity=fuel_capacity,
            cargo_hold_volume=cargo_hold_volume,
            deck_count=deck_count,
        )

    @property
    def weight_margin(self) -> float:
        """起飞与着陆重量差额 / Takeoff-landing weight margin.

        Returns:
            max_takeoff_weight - max_landing_weight.
        """
        return self.max_takeoff_weight - self.max_landing_weight

    def with_registration(self, registration: str) -> Aircraft:
        """创建不同注册号的航空器 / Create aircraft with different registration.

        Args:
            registration: 新注册号 / New registration number.

        Returns:
            新航空器实例 / New aircraft instance.
        """
        return Aircraft(
            aircraft_type=self.aircraft_type,
            registration=registration,
            max_takeoff_weight=self.max_takeoff_weight,
            max_landing_weight=self.max_landing_weight,
            max_zero_fuel_weight=self.max_zero_fuel_weight,
            fuel_capacity=self.fuel_capacity,
            cargo_hold_volume=self.cargo_hold_volume,
            deck_count=self.deck_count,
        )
