"""最大客舱载荷指数模型 / Max Cabin Load Index Model.

定义各甲板和飞行阶段的客舱载荷指数上限。
Defines the cabin load index upper bound for each deck
and flight phase.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FlightPhase(Enum):
    """飞行阶段 / Flight phase.

    描述飞机当前所处的飞行阶段。
    Describes the current flight phase of the aircraft.
    """

    TAKEOFF = "takeoff"
    """起飞 / Takeoff."""

    CLIMB = "climb"
    """爬升 / Climb."""

    CRUISE = "cruise"
    """巡航 / Cruise."""

    DESCENT = "descent"
    """下降 / Descent."""

    LANDING = "landing"
    """着陆 / Landing."""


class DeckType(Enum):
    """甲板类型 / Deck type.

    描述飞机货舱甲板的类型。
    Describes the type of aircraft cargo deck.
    """

    MAIN_DECK = "main_deck"
    """主甲板 / Main deck."""

    LOWER_DECK = "lower_deck"
    """下甲板 / Lower deck."""

    UPPER_DECK = "upper_deck"
    """上甲板 / Upper deck."""


@dataclass(frozen=True)
class MaxCLIM:
    """最大客舱载荷指数 / Max Cabin Load Index.

    表示特定甲板在特定飞行阶段下的最大客舱载荷指数
    (CLIM)，用于约束客舱货物装载方案。
    Represents the maximum Cabin Load Index (CLIM) for
    a specific deck during a specific flight phase, used
    to constrain cabin cargo loading plans.

    Attributes:
        clim_value: 最大CLIM值 / Max CLIM value.
        deck: 甲板类型 / Deck type.
        flight_phase: 飞行阶段 / Flight phase.
    """

    clim_value: float
    deck: DeckType
    flight_phase: FlightPhase

    @staticmethod
    def create(
        *,
        clim_value: float,
        deck: DeckType,
        flight_phase: FlightPhase,
    ) -> MaxCLIM:
        """创建最大CLIM / Create max CLIM.

        Args:
            clim_value: 最大CLIM值 / Max CLIM value.
            deck: 甲板类型 / Deck type.
            flight_phase: 飞行阶段 / Flight phase.

        Returns:
            最大CLIM实例 / MaxCLIM instance.
        """
        return MaxCLIM(
            clim_value=clim_value,
            deck=deck,
            flight_phase=flight_phase,
        )

    def allows_load_index(self, load_index: float) -> bool:
        """检查载荷指数是否允许。

        Check whether the given load index is allowed.

        Args:
            load_index: 当前载荷指数。/ Current load index.

        Returns:
            若载荷指数不超过CLIM上限则返回 True。
            True if load index does not exceed CLIM limit.
        """
        return load_index <= self.clim_value

    def margin(self, load_index: float) -> float:
        """计算CLIM余量 / Calculate CLIM margin.

        Args:
            load_index: 当前载荷指数。/ Current load index.

        Returns:
            距CLIM上限的余量，负值表示超限。
            Margin to CLIM limit; negative means exceeding.
        """
        return self.clim_value - load_index

    @property
    def is_takeoff_critical(self) -> bool:
        """是否为起飞关键阶段 / Is takeoff-critical phase.

        Returns:
            起飞或着陆阶段返回 True。
            True for takeoff or landing phases.
        """
        return self.flight_phase in (
            FlightPhase.TAKEOFF,
            FlightPhase.LANDING,
        )
