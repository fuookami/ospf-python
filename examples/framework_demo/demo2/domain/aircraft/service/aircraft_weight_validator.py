"""航空器重量校验器 / Aircraft weight validator.

校验航空器在各飞行阶段的重量约束。
Validates aircraft weight constraints per flight phase.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from examples.framework_demo.demo2.domain.aircraft.model.flight_phase import (
    FlightPhase,
)
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.aircraft.model.aircraft import Aircraft


@dataclass(frozen=True)
class WeightValidationResult:
    """重量校验结果 / Weight validation result.

    Attributes:
        is_valid: 是否有效 / Whether valid.
        actual_weight: 实际重量 (kg) / Actual weight (kg).
        limit_weight: 限制重量 (kg) / Limit weight (kg).
        margin: 余量 (kg) / Margin (kg).
        phase: 飞行阶段 / Flight phase.
    """

    is_valid: bool
    """是否有效 / Whether valid."""

    actual_weight: float
    """实际重量 (kg) / Actual weight (kg)."""

    limit_weight: float
    """限制重量 (kg) / Limit weight (kg)."""

    margin: float
    """余量 (kg) / Margin (kg)."""

    phase: FlightPhase
    """飞行阶段 / Flight phase."""


class AircraftWeightValidator:
    """航空器重量校验器 / Aircraft weight validator.

    按飞行阶段校验航空器重量是否超出结构限制。
    Validates aircraft weight against structural limits
    per flight phase.
    """

    def validate_takeoff(
        self,
        *,
        aircraft: Aircraft,
        current_weight: float,
    ) -> Result[WeightValidationResult, str, Err[str]]:
        """校验起飞重量 / Validate takeoff weight.

        Args:
            aircraft: 航空器 / Aircraft.
            current_weight: 当前总重量 (kg) / Current total weight (kg).

        Returns:
            校验结果 / Validation result.
        """
        limit = aircraft.max_takeoff_weight
        margin = limit - current_weight
        is_valid = current_weight <= limit
        result = WeightValidationResult(
            is_valid=is_valid,
            actual_weight=current_weight,
            limit_weight=limit,
            margin=margin,
            phase=FlightPhase.TAKEOFF,
        )
        if is_valid:
            return Ok(result)
        return Failed(
            Err(
                _code=ErrorCode.OUT_OF_RANGE,
                _message=(
                    f"Takeoff weight {current_weight:.1f} kg exceeds "
                    f"MTOW {limit:.1f} kg for {aircraft.registration}"
                ),
            )
        )

    def validate_landing(
        self,
        *,
        aircraft: Aircraft,
        current_weight: float,
    ) -> Result[WeightValidationResult, str, Err[str]]:
        """校验着陆重量 / Validate landing weight.

        Args:
            aircraft: 航空器 / Aircraft.
            current_weight: 当前总重量 (kg) / Current total weight (kg).

        Returns:
            校验结果 / Validation result.
        """
        limit = aircraft.max_landing_weight
        margin = limit - current_weight
        is_valid = current_weight <= limit
        result = WeightValidationResult(
            is_valid=is_valid,
            actual_weight=current_weight,
            limit_weight=limit,
            margin=margin,
            phase=FlightPhase.LANDING,
        )
        if is_valid:
            return Ok(result)
        return Failed(
            Err(
                _code=ErrorCode.OUT_OF_RANGE,
                _message=(
                    f"Landing weight {current_weight:.1f} kg exceeds "
                    f"MLW {limit:.1f} kg for {aircraft.registration}"
                ),
            )
        )

    def validate_zero_fuel(
        self,
        *,
        aircraft: Aircraft,
        current_weight: float,
    ) -> Result[WeightValidationResult, str, Err[str]]:
        """校验零油重量 / Validate zero fuel weight.

        Args:
            aircraft: 航空器 / Aircraft.
            current_weight: 当前零油重量 (kg) / Current zero fuel weight (kg).

        Returns:
            校验结果 / Validation result.
        """
        limit = aircraft.max_zero_fuel_weight
        margin = limit - current_weight
        is_valid = current_weight <= limit
        result = WeightValidationResult(
            is_valid=is_valid,
            actual_weight=current_weight,
            limit_weight=limit,
            margin=margin,
            phase=FlightPhase.CRUISE,
        )
        if is_valid:
            return Ok(result)
        return Failed(
            Err(
                _code=ErrorCode.OUT_OF_RANGE,
                _message=(
                    f"Zero fuel weight {current_weight:.1f} kg exceeds "
                    f"MZFW {limit:.1f} kg for {aircraft.registration}"
                ),
            )
        )

    def validate_for_phase(
        self,
        *,
        aircraft: Aircraft,
        current_weight: float,
        phase: FlightPhase,
    ) -> Result[WeightValidationResult, str, Err[str]]:
        """按阶段校验重量 / Validate weight for specific phase.

        根据飞行阶段自动选择对应的重量限制进行校验。
        Automatically selects the corresponding weight limit
        based on flight phase.

        Args:
            aircraft: 航空器 / Aircraft.
            current_weight: 当前重量 (kg) / Current weight (kg).
            phase: 飞行阶段 / Flight phase.

        Returns:
            校验结果 / Validation result.
        """
        limit_map = {
            FlightPhase.TAKEOFF: aircraft.max_takeoff_weight,
            FlightPhase.CLIMB: aircraft.max_takeoff_weight,
            FlightPhase.CRUISE: aircraft.max_zero_fuel_weight,
            FlightPhase.DESCENT: aircraft.max_landing_weight,
            FlightPhase.LANDING: aircraft.max_landing_weight,
        }
        limit = limit_map[phase]
        margin = limit - current_weight
        is_valid = current_weight <= limit
        result = WeightValidationResult(
            is_valid=is_valid,
            actual_weight=current_weight,
            limit_weight=limit,
            margin=margin,
            phase=phase,
        )
        if is_valid:
            return Ok(result)
        return Failed(
            Err(
                _code=ErrorCode.OUT_OF_RANGE,
                _message=(
                    f"Weight {current_weight:.1f} kg exceeds "
                    f"limit {limit:.1f} kg at phase "
                    f"{phase.value} for {aircraft.registration}"
                ),
            )
        )
