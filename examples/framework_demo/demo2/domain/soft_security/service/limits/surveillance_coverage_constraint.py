"""监控覆盖约束 / Surveillance coverage constraint.

确保监控覆盖率满足安全要求。
Ensures that surveillance coverage meets security
requirements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.soft_security_measure import MeasureType
from ...model.soft_security_result import SoftSecurityResult

if TYPE_CHECKING:
    from ...model.soft_security_measure import SoftSecurityMeasure


@dataclass(frozen=True)
class SurveillanceZone:
    """监控区域 / Surveillance zone.

    定义一个需要监控覆盖的区域及其最低覆盖率。
    Defines a zone requiring surveillance coverage
    and its minimum coverage threshold.

    Attributes:
        zone_id: 区域标识 / Zone identifier.
        min_coverage: 最低覆盖率 (0.0~1.0) /
            Minimum coverage ratio (0.0~1.0).
        priority: 区域优先级 (越高越重要) /
            Zone priority (higher = more important).
    """

    zone_id: str
    min_coverage: float = 0.9
    priority: int = 1


@dataclass(frozen=True)
class SurveillanceCoverageConstraint:
    """监控覆盖约束 / Surveillance coverage constraint.

    校验各监控区域的监控措施覆盖率是否达标，并对高优先级
    区域施加更严格的覆盖要求。
    Validates that surveillance measure coverage in each
    zone meets the threshold, applying stricter requirements
    to higher-priority zones.

    Attributes:
        zones: 监控区域列表 / List of surveillance zones.
        priority_bonus: 每级优先级额外覆盖率要求 /
            Extra coverage per priority level.
    """

    zones: tuple[SurveillanceZone, ...]
    priority_bonus: float = 0.02

    def evaluate(
        self,
        measures: tuple[SoftSecurityMeasure, ...],
    ) -> tuple[bool, SoftSecurityResult]:
        """评估监控覆盖合规性。

        Evaluate surveillance coverage compliance.

        Args:
            measures: 所有安全措施 / All security measures.

        Returns:
            tuple: (是否合规, 评估结果) /
                (compliant, evaluation result).
        """
        violations: list[str] = []
        sv_measures = [
            m
            for m in measures
            if m.measure_type == MeasureType.SURVEILLANCE and m.active
        ]

        for zone in self.zones:
            zone_ms = [m for m in sv_measures if m.zone == zone.zone_id]
            if not zone_ms:
                violations.append(f"no_surveillance:{zone.zone_id}")
                continue

            coverage = sum(m.effectiveness for m in zone_ms) / len(zone_ms)
            adjusted_min = min(
                1.0,
                zone.min_coverage + zone.priority * self.priority_bonus,
            )

            if coverage < adjusted_min:
                violations.append(
                    f"insufficient_coverage:{zone.zone_id}:"
                    f"{coverage:.2f}<{adjusted_min:.2f}"
                )

        all_ids = tuple(m.measure_id for m in sv_measures)
        total_cost = sum(m.cost for m in sv_measures)
        avg_eff = (
            sum(m.effectiveness for m in sv_measures) / len(sv_measures)
            if sv_measures
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

    def coverage_map(
        self,
        measures: tuple[SoftSecurityMeasure, ...],
    ) -> dict[str, float]:
        """按区域计算覆盖率 / Per-zone coverage ratio.

        Args:
            measures: 所有安全措施 / All security measures.

        Returns:
            区域标识到覆盖率的映射。
            Mapping of zone ID to coverage ratio.
        """
        sv_measures = [
            m
            for m in measures
            if m.measure_type == MeasureType.SURVEILLANCE and m.active
        ]
        result: dict[str, float] = {}
        for zone in self.zones:
            zone_ms = [m for m in sv_measures if m.zone == zone.zone_id]
            if not zone_ms:
                result[zone.zone_id] = 0.0
            else:
                result[zone.zone_id] = sum(m.effectiveness for m in zone_ms) / len(
                    zone_ms
                )
        return result

    def gap_map(
        self,
        measures: tuple[SoftSecurityMeasure, ...],
    ) -> dict[str, float]:
        """按区域计算覆盖率差距 / Per-zone coverage gap.

        Args:
            measures: 所有安全措施 / All security measures.

        Returns:
            区域标识到覆盖率差距的映射（正数表示不足）。
            Mapping of zone ID to coverage gap (positive = deficit).
        """
        coverage = self.coverage_map(measures)
        result: dict[str, float] = {}
        for zone in self.zones:
            required = min(
                1.0,
                zone.min_coverage + zone.priority * self.priority_bonus,
            )
            gap = required - coverage.get(zone.zone_id, 0.0)
            result[zone.zone_id] = max(0.0, gap)
        return result
