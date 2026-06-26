"""安全检查约束 / Security screening constraint.

验证货物安全检查等级是否满足要求。
Validates that cargo security screening level meets
the requirement.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...model.airworthiness_result import AirworthinessResult
from ...model.security_level import SecurityLevel


@dataclass(frozen=True)
class SecurityScreeningConstraint:
    """安全检查约束 / Security screening constraint.

    校验货物的实际安全检查等级是否达到了当前安全环境
    下要求的最低等级，确保所有货物经过充分的安全检查。
    Validates that the cargo's actual security screening level
    meets the minimum required level under the current security
    environment, ensuring all cargo has been thoroughly screened.

    Attributes:
        cargo_level: 货物实际安全等级 / Cargo actual security level.
        required_level: 要求的最低安全等级 / Required minimum level.
        cargo_id: 货物标识 / Cargo identifier.
    """

    cargo_level: SecurityLevel
    required_level: SecurityLevel
    cargo_id: str

    def check(self) -> AirworthinessResult:
        """执行安全检查校验 / Perform screening check.

        Returns:
            校验结果 / Validation result.
        """
        violations: list[str] = []
        margins: dict[str, float] = {}

        level_gap = self.cargo_level.value - self.required_level.value
        margins[f"security:{self.cargo_id}:level_gap"] = float(level_gap)
        margins[f"security:{self.cargo_id}:cargo_level"] = float(self.cargo_level.value)

        if not self.cargo_level.meets_requirement(self.required_level):
            violations.append(
                f"security_insufficient:"
                f"{self.cargo_id}:"
                f"actual={self.cargo_level.label_en}:"
                f"required={self.required_level.label_en}"
            )

        # 等级刚好满足时警告
        if level_gap == 0 and self.required_level >= SecurityLevel.HIGH:
            return AirworthinessResult.create_warning(
                violations=(
                    f"security_at_minimum:"
                    f"{self.cargo_id}:"
                    f"level={self.cargo_level.label_en}",
                ),
                margins=margins,
            )

        if violations:
            return AirworthinessResult.create_fail(
                violations=tuple(violations),
                margins=margins,
            )

        return AirworthinessResult.create_pass(margins=margins)
