"""货物限动装置定义 / Cargo restraint definition.

定义货物限动装置的类型和承载能力。
Defines the type and load-bearing capacity of cargo
restraint devices.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RestraintDirection(Enum):
    """限动方向 / Restraint direction.

    描述限动装置约束力的方向。
    Describes the direction of restraint force.
    """

    FORWARD = "forward"
    """前向 / Forward (toward nose)."""

    AFT = "aft"
    """后向 / Aft (toward tail)."""

    LATERAL_LEFT = "lateral_left"
    """左侧向 / Lateral left."""

    LATERAL_RIGHT = "lateral_right"
    """右侧向 / Lateral right."""

    VERTICAL_UP = "vertical_up"
    """垂直向上 / Vertical up."""

    VERTICAL_DOWN = "vertical_down"
    """垂直向下 / Vertical down."""


class RestraintType(Enum):
    """限动装置类型 / Restraint type.

    描述限动装置的物理类型。
    Describes the physical type of a restraint device.
    """

    CARGO_NET = "cargo_net"
    """货网 / Cargo net."""

    TIE_DOWN_STRAP = "tie_down_strap"
    """系留带 / Tie-down strap."""

    LOCK_MECHANISM = "lock_mechanism"
    """锁定机构 / Lock mechanism."""

    STOP_BLOCK = "stop_block"
    """止挡块 / Stop block."""

    PALLET_LOCK = "pallet_lock"
    """货盘锁 / Pallet lock."""


@dataclass(frozen=True)
class CargoRestraint:
    """货物限动装置 / Cargo restraint.

    描述一个货物限动装置的类型、最大承受过载力和约束方向，
    用于验证货物在各方向上的限动是否满足飞行安全要求。
    Describes a cargo restraint device's type, maximum G-force
    capacity, and restraint direction, used to verify that cargo
    restraint meets flight safety requirements in each direction.

    Attributes:
        restraint_type: 限动装置类型 / Restraint type.
        max_g_force: 最大承受过载(G) / Max G-force tolerance (G).
        direction: 限动方向 / Restraint direction.
    """

    restraint_type: RestraintType
    max_g_force: float
    direction: RestraintDirection

    @staticmethod
    def create(
        *,
        restraint_type: RestraintType,
        max_g_force: float,
        direction: RestraintDirection,
    ) -> CargoRestraint:
        """创建限动装置 / Create cargo restraint.

        Args:
            restraint_type: 限动装置类型 / Restraint type.
            max_g_force: 最大过载(G) / Max G-force (G).
            direction: 限动方向 / Restraint direction.

        Returns:
            限动装置实例 / CargoRestraint instance.
        """
        return CargoRestraint(
            restraint_type=restraint_type,
            max_g_force=max_g_force,
            direction=direction,
        )

    def withstands_g_force(self, g_force: float) -> bool:
        """检查是否能承受过载力。

        Check whether the restraint can withstand
        the given G-force.

        Args:
            g_force: 实际过载力(G)。/ Actual G-force (G).

        Returns:
            若过载力不超过最大承受值则返回 True。
            True if G-force does not exceed max tolerance.
        """
        return g_force <= self.max_g_force

    def margin(self, g_force: float) -> float:
        """计算过载余量 / Calculate G-force margin.

        Args:
            g_force: 实际过载力(G)。/ Actual G-force (G).

        Returns:
            距最大承受值的余量(G)，负值表示超出。
            Margin to max tolerance (G); negative means exceeding.
        """
        return self.max_g_force - g_force

    def restraint_force(self, cargo_mass: float, g_force: float) -> float:
        """计算限动所需力 / Calculate required restraint force.

        Args:
            cargo_mass: 货物质量(kg)。/ Cargo mass (kg).
            g_force: 过载系数(G)。/ G-force coefficient (G).

        Returns:
            限动所需力(N) = 质量 * 过载 * 9.81。
            Required restraint force (N) = mass * G * 9.81.
        """
        return cargo_mass * g_force * 9.81

    def is_vertical(self) -> bool:
        """是否为垂直方向 / Is vertical direction.

        Returns:
            垂直方向返回 True。
            True for vertical directions.
        """
        return self.direction in (
            RestraintDirection.VERTICAL_UP,
            RestraintDirection.VERTICAL_DOWN,
        )
