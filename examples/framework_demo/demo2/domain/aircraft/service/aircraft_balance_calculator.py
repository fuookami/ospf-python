"""航空器平衡计算器 / Aircraft balance calculator.

计算航空器重心 (Center of Gravity) 位置。
Computes aircraft center of gravity position.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from examples.framework_demo.demo2.domain.aircraft.model.position import Position

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.aircraft.model.aircraft import Aircraft


@dataclass(frozen=True)
class CGBalanceResult:
    """重心计算结果 / CG balance result.

    Attributes:
        cg_position: 重心位置 / CG position.
        total_weight: 总重量 (kg) / Total weight (kg).
        is_balanced: 是否在平衡范围内 / Whether within balance range.
        offset_from_ref: 距参考点偏移 (m) / Offset from reference (m).
    """

    cg_position: Position
    """重心位置 / CG position."""

    total_weight: float
    """总重量 (kg) / Total weight (kg)."""

    is_balanced: bool
    """是否在平衡范围内 / Whether within balance range."""

    offset_from_ref: float
    """距参考点偏移 (m) / Offset from reference (m)."""


@dataclass(frozen=True)
class LoadItem:
    """载荷项 / Load item.

    用于重心计算的单项载荷描述。
    Describes a single load item for CG calculation.

    Attributes:
        weight: 重量 (kg) / Weight (kg).
        position: 位置 / Position.
        item_id: 标识 / Identifier.
    """

    weight: float
    """重量 (kg) / Weight (kg)."""

    position: Position
    """位置 / Position."""

    item_id: str
    """标识 / Identifier."""


class AircraftBalanceCalculator:
    """航空器平衡计算器 / Aircraft balance calculator.

    根据各载荷项的位置和重量，计算航空器合成重心，
    并判断是否在允许的平衡范围内。
    Computes the composite CG of an aircraft based on
    individual load positions and weights, and checks
    whether it falls within the allowable balance range.
    """

    def calculate_cg(
        self,
        *,
        aircraft: Aircraft,
        loads: tuple[LoadItem, ...],
        empty_weight: float,
        empty_cg_x: float,
        fuel_weight: float,
        fuel_cg_x: float,
        max_cg_offset: float,
    ) -> CGBalanceResult:
        """计算重心位置 / Calculate CG position.

        使用力矩平衡法计算合成重心。
        Uses moment balance method to compute composite CG.

        Args:
            aircraft: 航空器 / Aircraft.
            loads: 载荷项列表 / List of load items.
            empty_weight: 空机重量 (kg) / Empty weight (kg).
            empty_cg_x: 空机重心纵向坐标 (m) / Empty CG x-coordinate (m).
            fuel_weight: 燃油重量 (kg) / Fuel weight (kg).
            fuel_cg_x: 燃油重心纵向坐标 (m) / Fuel CG x-coordinate (m).
            max_cg_offset: 最大允许偏移 (m) / Max allowable offset (m).

        Returns:
            重心计算结果 / CG balance result.
        """
        # 力矩累加: weight * position / Sum of moments
        total_moment_x = empty_weight * empty_cg_x + fuel_weight * fuel_cg_x
        total_moment_y = 0.0
        total_moment_z = 0.0
        total_weight = empty_weight + fuel_weight

        for load in loads:
            total_moment_x += load.weight * load.position.x
            total_moment_y += load.weight * load.position.y
            total_moment_z += load.weight * load.position.z
            total_weight += load.weight

        # 避免除零 / Avoid division by zero
        if total_weight == 0.0:
            return CGBalanceResult(
                cg_position=Position.origin(deck_id="default"),
                total_weight=0.0,
                is_balanced=True,
                offset_from_ref=0.0,
            )

        cg_x = total_moment_x / total_weight
        cg_y = total_moment_y / total_weight
        cg_z = total_moment_z / total_weight

        # 偏移量以空机重心为参考 / Offset relative to empty CG
        offset = abs(cg_x - empty_cg_x)
        is_balanced = offset <= max_cg_offset

        return CGBalanceResult(
            cg_position=Position.create(
                x=cg_x,
                y=cg_y,
                z=cg_z,
                deck_id="composite",
            ),
            total_weight=total_weight,
            is_balanced=is_balanced,
            offset_from_ref=offset,
        )

    def calculate_required_ballast(
        self,
        *,
        current_cg_x: float,
        target_cg_x: float,
        total_weight: float,
        ballast_position_x: float,
    ) -> float:
        """计算所需压舱物重量 / Calculate required ballast weight.

        通过力矩方程反推将重心调整到目标位置所需的压舱物重量。
        Derives ballast weight needed to shift CG to target
        via moment equation.

        Args:
            current_cg_x: 当前重心纵向坐标 (m) / Current CG x (m).
            target_cg_x: 目标重心纵向坐标 (m) / Target CG x (m).
            total_weight: 当前总重量 (kg) / Current total weight (kg).
            ballast_position_x: 压舱物放置位置 (m) / Ballast position x (m).

        Returns:
            所需压舱物重量 (kg)，负值表示需要减重 /
            Required ballast weight (kg), negative means weight removal.
        """
        # moment_balance: total * current + ballast * pos = (total + ballast) * target
        # ballast * (pos - target) = total * (target - current)
        denominator = ballast_position_x - target_cg_x
        if denominator == 0.0:
            return 0.0
        return total_weight * (target_cg_x - current_cg_x) / denominator
