"""行李安检约束 / Baggage screening constraint.

确保行李安检流程符合安全规范。
Ensures that baggage screening processes comply
with security regulations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.soft_security_measure import MeasureType
from ...model.soft_security_result import SoftSecurityResult

if TYPE_CHECKING:
    from ...model.soft_security_measure import SoftSecurityMeasure


@dataclass(frozen=True)
class ScreeningRequirement:
    """安检要求 / Screening requirement.

    描述行李安检通道的最低配置要求。
    Describes minimum configuration requirements for
    a baggage screening lane.

    Attributes:
        requirement_id: 要求标识 / Requirement identifier.
        min_effectiveness: 最低设备有效性 /
            Minimum equipment effectiveness.
        min_measure_count: 最低措施数量 /
            Minimum number of measures.
        lane: 所属安检通道 / Associated screening lane.
    """

    requirement_id: str
    min_effectiveness: float = 0.8
    min_measure_count: int = 2
    lane: str = ""


@dataclass(frozen=True)
class BaggageScreeningConstraint:
    """行李安检约束 / Baggage screening constraint.

    校验各安检通道是否配置了足够数量和有效性的安检措施，
    确保行李安检流程满足安全规范要求。
    Validates that each screening lane is equipped with
    a sufficient number of effective screening measures,
    ensuring baggage screening meets security requirements.

    Attributes:
        requirements: 安检要求列表 /
            List of screening requirements.
        global_min_effectiveness: 全局最低有效性 /
            Global minimum effectiveness.
    """

    requirements: tuple[ScreeningRequirement, ...]
    global_min_effectiveness: float = 0.6

    def evaluate(
        self,
        measures: tuple[SoftSecurityMeasure, ...],
    ) -> tuple[bool, SoftSecurityResult]:
        """评估行李安检合规性。

        Evaluate baggage screening compliance.

        Args:
            measures: 所有安全措施 / All security measures.

        Returns:
            tuple: (是否合规, 评估结果) /
                (compliant, evaluation result).
        """
        violations: list[str] = []
        bs_measures = [
            m
            for m in measures
            if m.measure_type == MeasureType.BAGGAGE_SCREENING and m.active
        ]

        for m in bs_measures:
            if m.effectiveness < self.global_min_effectiveness:
                violations.append(
                    f"low_screening_effectiveness:"
                    f"{m.measure_id}:"
                    f"{m.effectiveness:.2f}"
                    f"<{self.global_min_effectiveness:.2f}"
                )

        for req in self.requirements:
            lane_ms = (
                [m for m in bs_measures if m.zone == req.lane]
                if req.lane
                else bs_measures
            )

            if len(lane_ms) < req.min_measure_count:
                violations.append(
                    f"insufficient_screening_measures:"
                    f"{req.requirement_id}:"
                    f"{len(lane_ms)}<{req.min_measure_count}"
                )

            ineffective = [
                m for m in lane_ms if m.effectiveness < req.min_effectiveness
            ]
            if ineffective:
                violations.append(
                    f"screening_below_threshold:"
                    f"{req.requirement_id}:"
                    f"{len(ineffective)}_measures"
                )

        all_ids = tuple(m.measure_id for m in bs_measures)
        total_cost = sum(m.cost for m in bs_measures)
        avg_eff = (
            sum(m.effectiveness for m in bs_measures) / len(bs_measures)
            if bs_measures
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

    def lane_status(
        self,
        measures: tuple[SoftSecurityMeasure, ...],
    ) -> dict[str, dict[str, float | int]]:
        """按通道返回安检状态 / Per-lane screening status.

        Args:
            measures: 所有安全措施 / All security measures.

        Returns:
            通道标识到状态字典的映射，含 count、
            avg_effectiveness 字段。
            Mapping of lane ID to status dict with
            count and avg_effectiveness fields.
        """
        bs_measures = [
            m
            for m in measures
            if m.measure_type == MeasureType.BAGGAGE_SCREENING and m.active
        ]
        lanes: dict[str, list[SoftSecurityMeasure]] = {}
        for m in bs_measures:
            key = m.zone or "_global"
            lanes.setdefault(key, []).append(m)

        result: dict[str, dict[str, float | int]] = {}
        for lane_id, lane_ms in lanes.items():
            result[lane_id] = {
                "count": len(lane_ms),
                "avg_effectiveness": (
                    sum(m.effectiveness for m in lane_ms) / len(lane_ms)
                ),
                "total_cost": sum(m.cost for m in lane_ms),
            }
        return result
