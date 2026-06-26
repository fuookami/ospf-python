"""累积载荷约束 / Cumulative load constraint.

验证沿机身纵向的累积载荷是否超过结构限制。
Validates that the cumulative load along the aircraft
longitudinal axis does not exceed structural limits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.airworthiness_result import AirworthinessResult

if TYPE_CHECKING:
    from ...model.max_cumulative_load_weight import (
        MaxCumulativeLoadWeight,
    )


@dataclass(frozen=True)
class CumulativeLoadConstraint:
    """累积载荷约束 / Cumulative load constraint.

    校验在某一站位增加货物后，累积重量是否仍处于
    结构允许范围内，防止机身弯矩超限。
    Validates that after adding cargo at a station, the
    cumulative weight remains within the structural
    allowable range, preventing fuselage bending moment
    exceedance.

    Attributes:
        load_limit: 累积载荷限制 / Cumulative load limit.
        additional_weight: 新增重量(kg) / Additional weight (kg).
    """

    load_limit: MaxCumulativeLoadWeight
    additional_weight: float

    def check(self) -> AirworthinessResult:
        """执行累积载荷校验 / Perform cumulative load check.

        Returns:
            校验结果 / Validation result.
        """
        violations: list[str] = []
        margins: dict[str, float] = {}

        updated = self.load_limit.with_additional(self.additional_weight)
        margin = updated.margin()
        margins[f"cumulative:{self.load_limit.position}:margin"] = margin
        margins[f"cumulative:{self.load_limit.position}:utilization"] = (
            updated.utilization_ratio
        )

        if not self.load_limit.can_accommodate(self.additional_weight):
            violations.append(
                f"cumulative_overload:"
                f"pos={self.load_limit.position}:"
                f"{updated.cumulative:.1f}>"
                f"{self.load_limit.max_weight:.1f}"
            )

        # 接近限制时警告
        if 0 <= margin < self.load_limit.max_weight * 0.08:
            return AirworthinessResult.create_warning(
                violations=(
                    f"cumulative_near_limit:"
                    f"pos={self.load_limit.position}:"
                    f"margin={margin:.1f}kg",
                ),
                margins=margins,
            )

        if violations:
            return AirworthinessResult.create_fail(
                violations=tuple(violations),
                margins=margins,
            )

        return AirworthinessResult.create_pass(margins=margins)
