"""货物限动约束 / Cargo restraint constraint.

验证货物限动装置能否承受飞行中的过载力。
Validates that cargo restraint devices can withstand
the G-forces encountered during flight.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.airworthiness_result import AirworthinessResult

if TYPE_CHECKING:
    from ...model.cargo_restraint import CargoRestraint


@dataclass(frozen=True)
class CargoRestraintConstraint:
    """货物限动约束 / Cargo restraint constraint.

    校验指定货物的质量和飞行过载条件下，
    限动装置能否提供足够的约束力。
    Validates that the restraint device can provide
    sufficient restraining force for the given cargo
    mass and flight G-force conditions.

    Attributes:
        restraint: 限动装置 / Cargo restraint device.
        cargo_mass: 货物质量(kg) / Cargo mass (kg).
        required_g_force: 需承受的过载(G) /
            Required G-force tolerance (G).
    """

    restraint: CargoRestraint
    cargo_mass: float
    required_g_force: float

    def check(self) -> AirworthinessResult:
        """执行限动校验 / Perform restraint check.

        Returns:
            校验结果 / Validation result.
        """
        violations: list[str] = []
        margins: dict[str, float] = {}

        g_margin = self.restraint.margin(self.required_g_force)
        force_needed = self.restraint.restraint_force(
            self.cargo_mass, self.required_g_force
        )
        force_capacity = self.restraint.restraint_force(
            self.cargo_mass, self.restraint.max_g_force
        )
        force_margin = force_capacity - force_needed

        margins[f"restraint:{self.restraint.direction.value}:g_margin"] = g_margin
        margins[f"restraint:{self.restraint.direction.value}:force_margin"] = (
            force_margin
        )

        if not self.restraint.withstands_g_force(self.required_g_force):
            violations.append(
                f"restraint_exceeded:"
                f"{self.restraint.direction.value}:"
                f"{self.required_g_force:.1f}G>"
                f"{self.restraint.max_g_force:.1f}G"
            )

        # 接近极限时警告(余量 < 15%)
        if 0 <= g_margin < self.restraint.max_g_force * 0.15:
            return AirworthinessResult.create_warning(
                violations=(
                    f"restraint_near_limit:"
                    f"{self.restraint.direction.value}:"
                    f"g_margin={g_margin:.1f}G",
                ),
                margins=margins,
            )

        if violations:
            return AirworthinessResult.create_fail(
                violations=tuple(violations),
                margins=margins,
            )

        return AirworthinessResult.create_pass(margins=margins)
