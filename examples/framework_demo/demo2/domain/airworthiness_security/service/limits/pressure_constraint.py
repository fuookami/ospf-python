"""压力约束 / Pressure constraint.

验证货物是否能承受货舱压力差变化。
Validates that cargo can withstand the cargo hold
pressure differential changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ...model.airworthiness_result import AirworthinessResult


class PressureSensitivity(Enum):
    """压力敏感度 / Pressure sensitivity.

    货物对压力变化的敏感程度。
    Cargo sensitivity to pressure changes.
    """

    NONE = "none"
    """不敏感 / Not sensitive."""

    LOW = "low"
    """低敏感 / Low sensitivity."""

    MEDIUM = "medium"
    """中等敏感 / Medium sensitivity."""

    HIGH = "high"
    """高度敏感 / High sensitivity."""


# 各敏感度对应的最大可承受压差(kPa)
_MAX_PRESSURE_DIFF: dict[PressureSensitivity, float] = {
    PressureSensitivity.NONE: 101.3,
    PressureSensitivity.LOW: 60.0,
    PressureSensitivity.MEDIUM: 35.0,
    PressureSensitivity.HIGH: 15.0,
}


@dataclass(frozen=True)
class PressureConstraint:
    """压力约束 / Pressure constraint.

    校验货物的压力敏感度是否能在货舱压力差环境下
    安全运输，防止货物因压力变化损坏。
    Validates that the cargo's pressure sensitivity can be
    safely transported under the cargo hold pressure
    differential, preventing cargo damage from pressure
    changes.

    Attributes:
        cargo_id: 货物标识 / Cargo identifier.
        sensitivity: 货物压力敏感度 / Cargo pressure sensitivity.
        hold_pressure_diff: 货舱最大压差(kPa) /
            Cargo hold max pressure differential (kPa).
    """

    cargo_id: str
    sensitivity: PressureSensitivity
    hold_pressure_diff: float

    def check(self) -> AirworthinessResult:
        """执行压力校验 / Perform pressure check.

        Returns:
            校验结果 / Validation result.
        """
        violations: list[str] = []
        margins: dict[str, float] = {}

        max_allowed = _MAX_PRESSURE_DIFF[self.sensitivity]
        margin = max_allowed - self.hold_pressure_diff
        margins[f"pressure:{self.cargo_id}:margin"] = margin
        margins[f"pressure:{self.cargo_id}:max_allowed"] = max_allowed

        if self.hold_pressure_diff > max_allowed:
            violations.append(
                f"pressure_exceeded:"
                f"{self.cargo_id}:"
                f"sensitivity={self.sensitivity.value}:"
                f"hold_diff={self.hold_pressure_diff:.1f}kPa>"
                f"max_allowed={max_allowed:.1f}kPa"
            )

        # 高敏感货物余量不足时警告
        if self.sensitivity == PressureSensitivity.HIGH and 0 <= margin < 5.0:
            return AirworthinessResult.create_warning(
                violations=(
                    f"pressure_sensitive_near_limit:"
                    f"{self.cargo_id}:"
                    f"margin={margin:.1f}kPa",
                ),
                margins=margins,
            )

        # 中等敏感货物余量不足时也警告
        if self.sensitivity == PressureSensitivity.MEDIUM and 0 <= margin < 8.0:
            return AirworthinessResult.create_warning(
                violations=(
                    f"pressure_moderate_near_limit:"
                    f"{self.cargo_id}:"
                    f"margin={margin:.1f}kPa",
                ),
                margins=margins,
            )

        if violations:
            return AirworthinessResult.create_fail(
                violations=tuple(violations),
                margins=margins,
            )

        return AirworthinessResult.create_pass(margins=margins)
