"""访问控制区域约束 / Access control zone constraint.

确保各区域的访问控制措施达标。
Ensures that access control measures meet requirements
in each zone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.soft_security_measure import MeasureType
from ...model.soft_security_result import SoftSecurityResult

if TYPE_CHECKING:
    from ...model.soft_security_measure import SoftSecurityMeasure


@dataclass(frozen=True)
class AccessControlZone:
    """访问控制区域 / Access control zone.

    描述一个需要访问控制的物理区域及其最低要求。
    Describes a physical zone requiring access control
    and its minimum requirements.

    Attributes:
        zone_id: 区域标识 / Zone identifier.
        min_effectiveness: 最低有效性要求 /
            Minimum effectiveness requirement.
        required_measures: 必需的措施标识 /
            Required measure identifiers.
    """

    zone_id: str
    min_effectiveness: float = 0.7
    required_measures: tuple[str, ...] = ()


@dataclass(frozen=True)
class AccessControlConstraint:
    """访问控制区域约束 / Access control zone constraint.

    校验每个访问控制区域是否配置了充足的安全措施，
    且各措施的有效性不低于区域要求。
    Validates that each access control zone is equipped
    with sufficient security measures and that each
    measure meets the zone effectiveness requirement.

    Attributes:
        zones: 受控区域列表 / List of controlled zones.
    """

    zones: tuple[AccessControlZone, ...]

    def evaluate(
        self,
        measures: tuple[SoftSecurityMeasure, ...],
    ) -> tuple[bool, SoftSecurityResult]:
        """评估访问控制合规性。

        Evaluate access control compliance.

        Args:
            measures: 所有安全措施 / All security measures.

        Returns:
            tuple: (是否合规, 评估结果) /
                (compliant, evaluation result).
        """
        violations: list[str] = []
        ac_measures = [
            m
            for m in measures
            if m.measure_type == MeasureType.ACCESS_CONTROL and m.active
        ]

        for zone in self.zones:
            zone_measures = [m for m in ac_measures if m.zone == zone.zone_id]
            if not zone_measures:
                violations.append(f"no_access_control:{zone.zone_id}")
                continue

            for req_id in zone.required_measures:
                if not any(m.measure_id == req_id for m in zone_measures):
                    violations.append(f"missing_measure:{zone.zone_id}:{req_id}")

            for m in zone_measures:
                if m.effectiveness < zone.min_effectiveness:
                    violations.append(
                        f"low_zone_effectiveness:"
                        f"{zone.zone_id}:{m.measure_id}:"
                        f"{m.effectiveness:.2f}"
                        f"<{zone.min_effectiveness:.2f}"
                    )

        all_ids = tuple(m.measure_id for m in ac_measures)
        total_cost = sum(m.cost for m in ac_measures)
        avg_eff = (
            sum(m.effectiveness for m in ac_measures) / len(ac_measures)
            if ac_measures
            else 0.0
        )

        if violations:
            return (
                False,
                SoftSecurityResult.create_non_compliant(
                    score=avg_eff,
                    measures=all_ids,
                    violations=tuple(violations),
                    total_cost=total_cost,
                ),
            )

        return (
            True,
            SoftSecurityResult.create_compliant(
                score=avg_eff,
                measures=all_ids,
                total_cost=total_cost,
            ),
        )

    def zone_compliance(
        self,
        measures: tuple[SoftSecurityMeasure, ...],
    ) -> dict[str, bool]:
        """按区域返回合规状态 / Per-zone compliance status.

        Args:
            measures: 所有安全措施 / All security measures.

        Returns:
            区域标识到合规状态的映射。
            Mapping of zone ID to compliance status.
        """
        ac_measures = [
            m
            for m in measures
            if m.measure_type == MeasureType.ACCESS_CONTROL and m.active
        ]
        result: dict[str, bool] = {}
        for zone in self.zones:
            zone_ms = [m for m in ac_measures if m.zone == zone.zone_id]
            has_all = all(
                any(m.measure_id == rid for m in zone_ms)
                for rid in zone.required_measures
            )
            meets_eff = all(m.effectiveness >= zone.min_effectiveness for m in zone_ms)
            result[zone.zone_id] = bool(zone_ms) and has_all and meets_eff
        return result

    def missing_measures(
        self,
        measures: tuple[SoftSecurityMeasure, ...],
    ) -> dict[str, tuple[str, ...]]:
        """按区域返回缺失措施 / Per-zone missing measures.

        Args:
            measures: 所有安全措施 / All security measures.

        Returns:
            区域标识到缺失措施标识的映射。
            Mapping of zone ID to missing measure IDs.
        """
        ac_measures = [
            m
            for m in measures
            if m.measure_type == MeasureType.ACCESS_CONTROL and m.active
        ]
        result: dict[str, tuple[str, ...]] = {}
        for zone in self.zones:
            zone_ids = {m.measure_id for m in ac_measures if m.zone == zone.zone_id}
            missing = tuple(
                rid for rid in zone.required_measures if rid not in zone_ids
            )
            if missing:
                result[zone.zone_id] = missing
        return result
