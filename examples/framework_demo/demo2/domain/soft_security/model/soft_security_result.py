"""软安全分析结果 / Soft security analysis result.

定义软安全措施评估的结果数据结构。
Defines the result data structure for soft security
measure evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SoftSecurityResult:
    """软安全分析结果 / Soft security analysis result.

    汇总软安全措施评估的安全评分、已实施措施和合规状态，
    供上层应用决策使用。
    Summarizes the security score, implemented measures,
    and compliance status of soft security measure evaluation
    for upper-layer application decision-making.

    Attributes:
        score: 安全评分(0.0~1.0) / Security score (0.0~1.0).
        measures: 已实施措施标识元组 /
            Tuple of implemented measure identifiers.
        compliant: 是否满足安全要求 /
            Whether security requirements are met.
        violations: 违规描述元组 /
            Tuple of violation descriptions.
        total_cost: 总成本 / Total cost.
    """

    score: float
    measures: tuple[str, ...]
    compliant: bool
    violations: tuple[str, ...] = ()
    total_cost: float = 0.0

    @staticmethod
    def create_compliant(
        *,
        score: float,
        measures: tuple[str, ...] = (),
        total_cost: float = 0.0,
    ) -> SoftSecurityResult:
        """创建合规结果 / Create compliant result.

        Args:
            score: 安全评分 / Security score.
            measures: 已实施措施 / Implemented measures.
            total_cost: 总成本 / Total cost.

        Returns:
            合规的安全结果 / Compliant security result.
        """
        return SoftSecurityResult(
            score=min(1.0, max(0.0, score)),
            measures=measures,
            compliant=True,
            violations=(),
            total_cost=total_cost,
        )

    @staticmethod
    def create_non_compliant(
        *,
        score: float,
        measures: tuple[str, ...] = (),
        violations: tuple[str, ...] = (),
        total_cost: float = 0.0,
    ) -> SoftSecurityResult:
        """创建不合规结果 / Create non-compliant result.

        Args:
            score: 安全评分 / Security score.
            measures: 已实施措施 / Implemented measures.
            violations: 违规描述 / Violations.
            total_cost: 总成本 / Total cost.

        Returns:
            不合规的安全结果 / Non-compliant security result.
        """
        return SoftSecurityResult(
            score=min(1.0, max(0.0, score)),
            measures=measures,
            compliant=False,
            violations=violations,
            total_cost=total_cost,
        )

    @property
    def violation_count(self) -> int:
        """违规数量 / Violation count."""
        return len(self.violations)

    @property
    def measure_count(self) -> int:
        """措施数量 / Measure count."""
        return len(self.measures)

    @property
    def is_high_score(self) -> bool:
        """是否高分 / Is high score.

        Returns:
            评分大于等于 0.8 时返回 True。
            True if score is >= 0.8.
        """
        return self.score >= 0.8

    @property
    def cost_per_measure(self) -> float:
        """每措施平均成本 / Average cost per measure.

        Returns:
            平均成本，无措施时返回 0.0。
            Average cost; 0.0 if no measures.
        """
        if not self.measures:
            return 0.0
        return self.total_cost / len(self.measures)

    def has_measure(self, measure_id: str) -> bool:
        """检查是否包含特定措施。

        Check whether a specific measure is present.

        Args:
            measure_id: 措施标识 / Measure identifier.

        Returns:
            若包含该措施则返回 True。
            True if the measure is present.
        """
        return measure_id in self.measures

    def merge(
        self,
        other: SoftSecurityResult,
    ) -> SoftSecurityResult:
        """合并两个结果 / Merge two results.

        合并规则：取较低评分；任一不合规则不合规；
        合并措施和违规。

        Args:
            other: 另一个结果 / Another result.

        Returns:
            合并后的新结果 / New merged result.
        """
        merged_measures = tuple(dict.fromkeys(self.measures + other.measures))
        merged_violations = self.violations + other.violations
        return SoftSecurityResult(
            score=min(self.score, other.score),
            measures=merged_measures,
            compliant=self.compliant and other.compliant,
            violations=merged_violations,
            total_cost=self.total_cost + other.total_cost,
        )
