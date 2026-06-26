"""飞行阶段定义 / Flight phase definition.

航空器飞行阶段枚举，用于不同阶段的重量限制校验。
Aircraft flight phase enumeration for weight limit
validation across phases.
"""

from __future__ import annotations

import enum


class FlightPhase(enum.Enum):
    """飞行阶段 / Flight phase.

    描述航空器飞行过程中的各阶段，不同阶段对应
    不同的重量和平衡限制。
    Describes phases during aircraft flight; each phase
    has different weight and balance constraints.

    Attributes:
        value: 阶段名称 / Phase name.
    """

    TAKEOFF = "takeoff"
    """起飞阶段 / Takeoff phase.

    起飞时受最大起飞重量限制。
    Subject to max takeoff weight during takeoff.
    """

    CLIMB = "climb"
    """爬升阶段 / Climb phase.

    爬升过程中燃油持续消耗，重量递减。
    Fuel is consumed continuously, weight decreases.
    """

    CRUISE = "cruise"
    """巡航阶段 / Cruise phase.

    巡航阶段燃油消耗最为稳定。
    Steady fuel consumption during cruise.
    """

    DESCENT = "descent"
    """下降阶段 / Descent phase.

    下降阶段推力减小，燃油消耗降低。
    Reduced thrust, lower fuel consumption during descent.
    """

    LANDING = "landing"
    """着陆阶段 / Landing phase.

    着陆时受最大着陆重量限制。
    Subject to max landing weight during landing.
    """

    @property
    def weight_limit_factor(self) -> float:
        """重量限制系数 / Weight limit factor.

        不同阶段对最大结构重量的允许比例。
        The allowable fraction of max structural weight
        for each phase.

        Returns:
            重量限制系数 (0.0-1.0) / Weight limit factor.
        """
        factors = {
            FlightPhase.TAKEOFF: 1.0,
            FlightPhase.CLIMB: 0.98,
            FlightPhase.CRUISE: 0.95,
            FlightPhase.DESCENT: 0.90,
            FlightPhase.LANDING: 0.85,
        }
        return factors[self]

    @property
    def is_ground_phase(self) -> bool:
        """是否为地面阶段 / Whether this is a ground phase.

        Returns:
            起飞和着陆为地面阶段 / True for takeoff and landing.
        """
        return self in (FlightPhase.TAKEOFF, FlightPhase.LANDING)
