"""危险品适航约束 / Hazmat airworthiness constraint.

验证危险品货物是否满足适航法规要求。
Validates that hazardous material cargo meets
airworthiness regulatory requirements.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ...model.airworthiness_result import AirworthinessResult
from ...model.security_level import SecurityLevel


class HazmatClass(Enum):
    """危险品类别 / Hazardous material class.

    IATA 危险品类别划分。
    IATA dangerous goods classification.
    """

    CLASS_1 = "explosives"
    """爆炸品 / Explosives."""

    CLASS_2 = "gases"
    """气体 / Gases."""

    CLASS_3 = "flammable_liquids"
    """易燃液体 / Flammable liquids."""

    CLASS_4 = "flammable_solids"
    """易燃固体 / Flammable solids."""

    CLASS_5 = "oxidizers"
    """氧化剂 / Oxidizers."""

    CLASS_6 = "toxic"
    """毒性物质 / Toxic substances."""

    CLASS_7 = "radioactive"
    """放射性物质 / Radioactive materials."""

    CLASS_8 = "corrosives"
    """腐蚀性物质 / Corrosives."""

    CLASS_9 = "miscellaneous"
    """杂项危险品 / Miscellaneous dangerous goods."""


# 需要最高等级安全检查的危险品类别
_MAXIMUM_SCREENING_CLASSES: frozenset[HazmatClass] = frozenset(
    (
        HazmatClass.CLASS_1,
        HazmatClass.CLASS_7,
    )
)

# 需要高等级安全检查的危险品类别
_HIGH_SCREENING_CLASSES: frozenset[HazmatClass] = frozenset(
    (
        HazmatClass.CLASS_2,
        HazmatClass.CLASS_5,
        HazmatClass.CLASS_6,
    )
)


@dataclass(frozen=True)
class HazmatAirworthinessConstraint:
    """危险品适航约束 / Hazmat airworthiness constraint.

    校验危险品货物的安全检查等级是否满足该品类在适航
    法规中的要求，并检查禁运品类。
    Validates that the security screening level of hazardous
    material cargo meets the airworthiness regulatory
    requirements for its class, and checks for prohibited
    classes.

    Attributes:
        hazmat_class: 危险品类别 / Hazardous material class.
        cargo_id: 货物标识 / Cargo identifier.
        cargo_security_level: 货物安全等级 / Cargo security level.
    """

    hazmat_class: HazmatClass
    cargo_id: str
    cargo_security_level: SecurityLevel

    @staticmethod
    def required_level_for_class(
        hazmat_class: HazmatClass,
    ) -> SecurityLevel:
        """获取品类要求的安全等级。

        Get the required security level for a hazmat class.

        Args:
            hazmat_class: 危险品类别。/ Hazardous material class.

        Returns:
            要求的安全等级。
            Required security level.
        """
        if hazmat_class in _MAXIMUM_SCREENING_CLASSES:
            return SecurityLevel.MAXIMUM
        if hazmat_class in _HIGH_SCREENING_CLASSES:
            return SecurityLevel.HIGH
        return SecurityLevel.ELEVATED

    def check(self) -> AirworthinessResult:
        """执行危险品适航校验 / Perform hazmat check.

        Returns:
            校验结果 / Validation result.
        """
        violations: list[str] = []
        margins: dict[str, float] = {}

        required = self.required_level_for_class(self.hazmat_class)
        level_gap = self.cargo_security_level.value - required.value
        margins[f"hazmat:{self.cargo_id}:level_gap"] = float(level_gap)
        margins[f"hazmat:{self.cargo_id}:required_level"] = float(required.value)

        if not self.cargo_security_level.meets_requirement(required):
            violations.append(
                f"hazmat_screening_insufficient:"
                f"{self.cargo_id}:"
                f"class={self.hazmat_class.value}:"
                f"actual={self.cargo_security_level.label_en}:"
                f"required={required.label_en}"
            )

        # 1类和7类本身也需要特别警告
        if self.hazmat_class in _MAXIMUM_SCREENING_CLASSES and level_gap == 0:
            return AirworthinessResult.create_warning(
                violations=(
                    f"hazmat_high_risk_at_minimum:"
                    f"{self.cargo_id}:"
                    f"class={self.hazmat_class.value}",
                ),
                margins=margins,
            )

        if violations:
            return AirworthinessResult.create_fail(
                violations=tuple(violations),
                margins=margins,
            )

        return AirworthinessResult.create_pass(margins=margins)
