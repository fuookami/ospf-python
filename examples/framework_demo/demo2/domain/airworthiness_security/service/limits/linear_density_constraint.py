"""线密度约束 / Linear density constraint.

验证货舱地板线密度分布是否在结构限制范围内。
Validates that the linear density distribution on the
cargo deck floor is within structural limits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.airworthiness_result import AirworthinessResult

if TYPE_CHECKING:
    from ...model.linear_density import LinearDensity


@dataclass(frozen=True)
class LinearDensityConstraint:
    """线密度约束 / Linear density constraint.

    校验指定段的线性载荷密度是否超过地板结构允许的
    最大线密度，防止地板局部过载。
    Validates that the linear load density of a specified
    segment does not exceed the floor structure's maximum
    allowable linear density, preventing local floor overload.

    Attributes:
        density: 当前线密度 / Current linear density.
        max_density: 最大允许线密度(kg/m) /
            Max allowable linear density (kg/m).
    """

    density: LinearDensity
    max_density: float

    def check(self) -> AirworthinessResult:
        """执行线密度校验 / Perform linear density check.

        Returns:
            校验结果 / Validation result.
        """
        violations: list[str] = []
        margins: dict[str, float] = {}

        margin = self.density.margin_to_limit(self.max_density)
        margins[f"linear_density:{self.density.position}:margin"] = margin
        margins[f"linear_density:{self.density.position}:total_mass"] = (
            self.density.total_mass
        )

        if self.density.exceeds_density(self.max_density):
            violations.append(
                f"density_exceeded:"
                f"pos={self.density.position}:"
                f"{self.density.density:.1f}>"
                f"{self.max_density:.1f}kg/m"
            )

        # 接近限制时警告(余量 < 10%)
        if 0 <= margin < self.max_density * 0.1:
            return AirworthinessResult.create_warning(
                violations=(
                    f"density_near_limit:"
                    f"pos={self.density.position}:"
                    f"margin={margin:.1f}kg/m",
                ),
                margins=margins,
            )

        if violations:
            return AirworthinessResult.create_fail(
                violations=tuple(violations),
                margins=margins,
            )

        return AirworthinessResult.create_pass(margins=margins)
