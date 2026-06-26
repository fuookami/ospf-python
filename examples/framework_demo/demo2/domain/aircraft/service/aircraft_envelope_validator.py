"""航空器包线校验器 / Aircraft envelope validator.

校验航空器运行状态是否在其操作包线内。
Validates that aircraft operating state is within
its operating envelope.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from examples.framework_demo.demo2.domain.aircraft.model.flight_phase import (
    FlightPhase,
)
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import (
    Failed,
    Ok,
    Result,
    Warn,
)

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.aircraft.model.aircraft import Aircraft
    from examples.framework_demo.demo2.domain.aircraft.model.aircraft_model import (
        AircraftModel,
    )


@dataclass(frozen=True)
class EnvelopePoint:
    """包线工作点 / Envelope operating point.

    描述航空器在某个时刻的操作状态。
    Describes aircraft operating state at a point in time.

    Attributes:
        weight: 当前重量 (kg) / Current weight (kg).
        phase: 飞行阶段 / Flight phase.
        altitude_ft: 飞行高度 (ft) / Altitude (ft).
        temperature_dev: 偏离标准温度 (°C) / Temperature deviation from ISA (°C).
    """

    weight: float
    """当前重量 (kg) / Current weight (kg)."""

    phase: FlightPhase
    """飞行阶段 / Flight phase."""

    altitude_ft: float
    """飞行高度 (ft) / Altitude (ft)."""

    temperature_dev: float
    """偏离标准温度 (°C) / Temperature deviation from ISA (°C)."""


@dataclass(frozen=True)
class EnvelopeCheckResult:
    """包线校验结果 / Envelope check result.

    Attributes:
        is_within_envelope: 是否在包线内 / Whether within envelope.
        weight_margin: 重量余量 (kg) / Weight margin (kg).
        warnings: 警告信息列表 / List of warning messages.
    """

    is_within_envelope: bool
    """是否在包线内 / Whether within envelope."""

    weight_margin: float
    """重量余量 (kg) / Weight margin (kg)."""

    warnings: tuple[str, ...]
    """警告信息列表 / List of warning messages."""


class AircraftEnvelopeValidator:
    """航空器包线校验器 / Aircraft envelope validator.

    校验航空器操作状态（重量、高度、温度偏差等）
    是否在其认证的操作包线范围内。
    Validates aircraft operating state (weight, altitude,
    temperature deviation, etc.) against its certified
    operating envelope.
    """

    # 标准操作包线限制 / Standard operating envelope limits
    _MAX_ALTITUDE_FT: float = 45000.0
    """最大认证高度 (ft) / Max certified altitude (ft)."""

    _MAX_TEMP_DEVIATION: float = 35.0
    """最大允许温度偏差 (°C) / Max allowable temperature deviation (°C)."""

    _WEIGHT_WARNING_RATIO: float = 0.95
    """重量警告阈值比例 / Weight warning threshold ratio."""

    def check_envelope(
        self,
        *,
        aircraft_model: AircraftModel,
        point: EnvelopePoint,
    ) -> Result[EnvelopeCheckResult, str, Err[str]]:
        """校验操作包线 / Check operating envelope.

        综合校验重量、高度和温度偏差是否在允许范围内。
        Comprehensively validates weight, altitude, and temperature
        deviation against allowable ranges.

        Args:
            aircraft_model: 航空器模型 / Aircraft model.
            point: 操作状态点 / Operating point.

        Returns:
            包线校验结果 / Envelope check result.
        """
        warnings: list[str] = []
        aircraft = aircraft_model.aircraft

        # 确定当前阶段的重量限制 / Determine weight limit for phase
        weight_limit = self._phase_weight_limit(aircraft, point.phase)
        weight_margin = weight_limit - point.weight

        if point.weight > weight_limit:
            return Failed(
                Err(
                    _code=ErrorCode.OUT_OF_RANGE,
                    _message=(
                        f"Weight {point.weight:.1f} kg exceeds "
                        f"envelope limit {weight_limit:.1f} kg "
                        f"at phase {point.phase.value}"
                    ),
                )
            )

        # 重量接近限制时发出警告 / Warn when weight nears limit
        warning_threshold = weight_limit * self._WEIGHT_WARNING_RATIO
        if point.weight > warning_threshold:
            warnings.append(
                f"Weight {point.weight:.1f} kg is within "
                f"{(1 - self._WEIGHT_WARNING_RATIO) * 100:.0f}% "
                f"of envelope limit {weight_limit:.1f} kg"
            )

        # 校验高度 / Check altitude
        if point.altitude_ft > self._MAX_ALTITUDE_FT:
            return Failed(
                Err(
                    _code=ErrorCode.OUT_OF_RANGE,
                    _message=(
                        f"Altitude {point.altitude_ft:.0f} ft exceeds "
                        f"max certified {self._MAX_ALTITUDE_FT:.0f} ft"
                    ),
                )
            )

        if point.altitude_ft > self._MAX_ALTITUDE_FT * 0.9:
            warnings.append(
                f"Altitude {point.altitude_ft:.0f} ft is near "
                f"certified ceiling {self._MAX_ALTITUDE_FT:.0f} ft"
            )

        # 校验温度偏差 / Check temperature deviation
        if abs(point.temperature_dev) > self._MAX_TEMP_DEVIATION:
            return Failed(
                Err(
                    _code=ErrorCode.OUT_OF_RANGE,
                    _message=(
                        f"Temperature deviation {point.temperature_dev:+.1f} C "
                        f"exceeds allowable "
                        f"+/-{self._MAX_TEMP_DEVIATION:.1f} C"
                    ),
                )
            )

        if abs(point.temperature_dev) > self._MAX_TEMP_DEVIATION * 0.8:
            warnings.append(
                f"Temperature deviation {point.temperature_dev:+.1f} C "
                f"is near allowable limit "
                f"+/-{self._MAX_TEMP_DEVIATION:.1f} C"
            )

        result = EnvelopeCheckResult(
            is_within_envelope=True,
            weight_margin=weight_margin,
            warnings=tuple(warnings),
        )

        if warnings:
            return Warn(result, self._build_warning_error(warnings))
        return Ok(result)

    def check_cg_envelope(
        self,
        *,
        cg_offset: float,
        max_cg_offset: float,
    ) -> Result[bool, str, Err[str]]:
        """校验重心包线 / Check CG envelope.

        Args:
            cg_offset: 当前重心偏移 (m) / Current CG offset (m).
            max_cg_offset: 最大允许偏移 (m) / Max allowable offset (m).

        Returns:
            校验结果 / Check result.
        """
        if abs(cg_offset) > max_cg_offset:
            return Failed(
                Err(
                    _code=ErrorCode.OUT_OF_RANGE,
                    _message=(
                        f"CG offset {cg_offset:.3f} m exceeds "
                        f"allowable +/-{max_cg_offset:.3f} m"
                    ),
                )
            )
        return Ok(True)

    def _phase_weight_limit(
        self,
        aircraft: Aircraft,
        phase: FlightPhase,
    ) -> float:
        """获取阶段重量限制 / Get phase weight limit.

        Args:
            aircraft: 航空器 / Aircraft.
            phase: 飞行阶段 / Flight phase.

        Returns:
            重量限制 (kg) / Weight limit (kg).
        """
        limit_map = {
            FlightPhase.TAKEOFF: aircraft.max_takeoff_weight,
            FlightPhase.CLIMB: aircraft.max_takeoff_weight,
            FlightPhase.CRUISE: aircraft.max_zero_fuel_weight,
            FlightPhase.DESCENT: aircraft.max_landing_weight,
            FlightPhase.LANDING: aircraft.max_landing_weight,
        }
        return limit_map[phase]

    def _build_warning_error(self, warnings: list[str]) -> Err[str]:
        """构建警告错误对象 / Build warning error object.

        Args:
            warnings: 警告信息列表 / Warning messages.

        Returns:
            警告错误 / Warning error.
        """
        return Err(
            _code=ErrorCode.OUT_OF_RANGE,
            _message="; ".join(warnings),
        )
