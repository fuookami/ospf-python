"""结构地板约束 / Structural floor constraint.

验证地板载荷是否在结构限制范围内。
Validates that floor loading is within structural limits.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...model.airworthiness_result import AirworthinessResult
from ...model.floor_loading import FloorLoading


@dataclass(frozen=True)
class StructuralFloorConstraint:
    """结构地板约束 / Structural floor constraint.

    校验指定区域的地板单位面积载荷是否超过结构极限，
    防止地板结构损伤。
    Validates that the per-square-meter floor load in a
    specified area does not exceed the structural limit,
    preventing floor structural damage.

    Attributes:
        floor_loading: 地板载荷限制 / Floor loading limit.
    """

    floor_loading: FloorLoading

    def check(self, applied_load_per_sqm: float) -> AirworthinessResult:
        """执行地板载荷校验 / Perform floor load check.

        Args:
            applied_load_per_sqm: 施加的单位面积载荷(kg/m^2)。
                Applied load per square meter (kg/m^2).

        Returns:
            校验结果 / Validation result.
        """
        violations: list[str] = []
        margins: dict[str, float] = {}

        projected = FloorLoading(
            area_id=self.floor_loading.area_id,
            max_load_per_sqm=self.floor_loading.max_load_per_sqm,
            current_load=(self.floor_loading.current_load + applied_load_per_sqm),
        )
        margin = projected.margin()
        margins[f"floor:{self.floor_loading.area_id}:margin"] = margin
        margins[f"floor:{self.floor_loading.area_id}:utilization"] = (
            projected.utilization_ratio
        )

        if not self.floor_loading.can_accommodate(applied_load_per_sqm):
            violations.append(
                f"floor_overload:{self.floor_loading.area_id}:"
                f"{projected.current_load:.1f}>"
                f"{self.floor_loading.max_load_per_sqm:.1f}"
            )

        # 接近限制时警告
        if 0 <= margin < self.floor_loading.max_load_per_sqm * 0.1:
            return AirworthinessResult.create_warning(
                violations=(
                    f"floor_near_limit:"
                    f"{self.floor_loading.area_id}:"
                    f"margin={margin:.1f}kg/m^2",
                ),
                margins=margins,
            )

        if violations:
            return AirworthinessResult.create_fail(
                violations=tuple(violations),
                margins=margins,
            )

        return AirworthinessResult.create_pass(margins=margins)
