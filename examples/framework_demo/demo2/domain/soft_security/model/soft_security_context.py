"""软安全上下文 / Soft security context.

管理软安全措施的注册与验证流程。
Manages registration and validation for soft security measures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .soft_security_aggregation import SoftSecurityAggregation
from .soft_security_result import SoftSecurityResult

if TYPE_CHECKING:
    from .soft_security_measure import SoftSecurityMeasure


@dataclass
class SoftSecurityContext:
    """软安全上下文 / Soft security context.

    提供可变的注册接口，收集安全措施和评估结果后可生成
    不可变的聚合对象并执行合规验证。
    Provides a mutable registration interface; after
    collecting security measures and evaluation results,
    generates an immutable aggregation object and performs
    compliance validation.

    Attributes:
        _measures: 已注册措施 / Registered measures.
        _results: 已注册结果 / Registered results.
        _min_score: 最低合规评分 / Minimum compliance score.
    """

    _measures: list[SoftSecurityMeasure] = field(
        default_factory=list,
        init=False,
    )
    _results: list[SoftSecurityResult] = field(
        default_factory=list,
        init=False,
    )
    _min_score: float = field(default=0.7, init=False)

    def register_measure(
        self,
        measure: SoftSecurityMeasure,
    ) -> None:
        """注册安全措施 / Register security measure.

        Args:
            measure: 软安全措施 / Soft security measure.
        """
        self._measures.append(measure)

    def register_result(
        self,
        result: SoftSecurityResult,
    ) -> None:
        """注册评估结果 / Register evaluation result.

        Args:
            result: 评估结果 / Evaluation result.
        """
        self._results.append(result)

    def set_min_score(self, score: float) -> None:
        """设置最低合规评分 / Set minimum compliance score.

        Args:
            score: 最低评分阈值 / Minimum score threshold.
        """
        self._min_score = min(1.0, max(0.0, score))

    @property
    def min_score(self) -> float:
        """最低合规评分 / Minimum compliance score."""
        return self._min_score

    @property
    def measure_count(self) -> int:
        """已注册措施数 / Registered measure count."""
        return len(self._measures)

    @property
    def result_count(self) -> int:
        """已注册结果数 / Registered result count."""
        return len(self._results)

    @property
    def active_measure_count(self) -> int:
        """已激活措施数 / Active measure count."""
        return sum(1 for m in self._measures if m.active)

    def find_measure(
        self,
        measure_id: str,
    ) -> SoftSecurityMeasure | None:
        """按标识查找措施 / Find measure by identifier.

        Args:
            measure_id: 措施标识 / Measure identifier.

        Returns:
            匹配的措施或 None。
            Matching measure, or None.
        """
        for m in self._measures:
            if m.measure_id == measure_id:
                return m
        return None

    def measures_by_zone(
        self,
        zone: str,
    ) -> tuple[SoftSecurityMeasure, ...]:
        """按区域筛选措施 / Filter measures by zone.

        Args:
            zone: 区域标识 / Zone identifier.

        Returns:
            属于该区域的措施元组。
            Tuple of measures in the specified zone.
        """
        return tuple(m for m in self._measures if m.zone == zone)

    def build_aggregation(self) -> SoftSecurityAggregation:
        """构建不可变聚合对象 / Build immutable aggregation.

        Returns:
            包含所有已注册数据的聚合对象。
            Aggregation with all registered data.
        """
        return SoftSecurityAggregation(
            results=tuple(self._results),
            measures=tuple(self._measures),
        )

    def validate(self) -> SoftSecurityResult:
        """执行合规验证 / Perform compliance validation.

        检查已激活措施的整体有效性和区域覆盖。
        Checks overall effectiveness and zone coverage
        of active measures.

        Returns:
            验证结果 / Validation result.
        """
        violations: list[str] = []
        active = [m for m in self._measures if m.active]

        if not active:
            violations.append("no_active_measures")
            return SoftSecurityResult.create_non_compliant(
                score=0.0,
                violations=tuple(violations),
            )

        total_effectiveness = sum(m.effectiveness for m in active)
        avg_effectiveness = total_effectiveness / len(active)

        zones: dict[str, list[SoftSecurityMeasure]] = {}
        for m in active:
            if m.zone:
                zones.setdefault(m.zone, []).append(m)

        for zone_id, zone_measures in zones.items():
            zone_score = sum(m.effectiveness for m in zone_measures) / len(
                zone_measures
            )
            if zone_score < self._min_score:
                violations.append(
                    f"zone_below_threshold:{zone_id}:"
                    f"{zone_score:.2f}<{self._min_score:.2f}"
                )

        for m in active:
            if m.effectiveness < 0.3:
                violations.append(
                    f"low_effectiveness:{m.measure_id}:{m.effectiveness:.2f}"
                )

        total_cost = sum(m.cost for m in active)
        measure_ids = tuple(m.measure_id for m in active)

        if violations:
            return SoftSecurityResult.create_non_compliant(
                score=avg_effectiveness,
                measures=measure_ids,
                violations=tuple(violations),
                total_cost=total_cost,
            )

        return SoftSecurityResult.create_compliant(
            score=avg_effectiveness,
            measures=measure_ids,
            total_cost=total_cost,
        )
