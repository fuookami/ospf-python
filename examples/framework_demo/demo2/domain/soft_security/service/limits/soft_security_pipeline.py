"""软安全评估管道 / Soft security evaluation pipeline.

组合所有软安全约束和目标为统一验证管道。
Composes all soft security constraints and objectives
into a unified validation pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ...model.soft_security_result import SoftSecurityResult

if TYPE_CHECKING:
    from ...model.soft_security_aggregation import (
        SoftSecurityAggregation,
    )
    from ...model.soft_security_context import SoftSecurityContext
    from ...model.soft_security_measure import SoftSecurityMeasure
    from .access_control_constraint import AccessControlConstraint
    from .baggage_screening_constraint import BaggageScreeningConstraint
    from .soft_security_cost_objective import SoftSecurityCostObjective
    from .surveillance_coverage_constraint import (
        SurveillanceCoverageConstraint,
    )


@dataclass(frozen=True)
class SoftSecurityPipelineConfig:
    """软安全管道配置 / Pipeline configuration.

    控制管道中启用哪些约束和目标。
    Controls which constraints and objectives are enabled.

    Attributes:
        enable_access_control: 启用访问控制约束 /
            Enable access control constraint.
        enable_surveillance: 启用监控覆盖约束 /
            Enable surveillance constraint.
        enable_baggage_screening: 启用行李安检约束 /
            Enable baggage screening constraint.
        enable_cost_objective: 启用成本优化目标 /
            Enable cost objective.
    """

    enable_access_control: bool = True
    enable_surveillance: bool = True
    enable_baggage_screening: bool = True
    enable_cost_objective: bool = True


@dataclass
class SoftSecurityPipeline:
    """软安全评估管道 / Soft security evaluation pipeline.

    按顺序执行访问控制、监控覆盖和行李安检约束检查，
    加上成本优化目标，合并结果返回。
    Executes access control, surveillance coverage, and
    baggage screening constraint checks in sequence, plus
    the cost objective, merging results for return.

    Attributes:
        context: 软安全上下文 / Soft security context.
        access_constraint: 访问控制约束 / Access control constraint.
        surveillance_constraint: 监控覆盖约束 /
            Surveillance coverage constraint.
        baggage_constraint: 行李安检约束 /
            Baggage screening constraint.
        cost_objective: 成本优化目标 / Cost objective.
        config: 管道配置 / Pipeline configuration.
        _results: 内部结果收集 / Internal result collection.
    """

    context: SoftSecurityContext
    access_constraint: AccessControlConstraint
    surveillance_constraint: SurveillanceCoverageConstraint
    baggage_constraint: BaggageScreeningConstraint
    cost_objective: SoftSecurityCostObjective
    config: SoftSecurityPipelineConfig = field(
        default_factory=SoftSecurityPipelineConfig,
    )
    _results: list[SoftSecurityResult] = field(
        default_factory=list,
        init=False,
    )

    def run(
        self,
        *,
        measures: tuple[SoftSecurityMeasure, ...],
    ) -> SoftSecurityResult:
        """运行软安全评估管道。

        Run the soft security evaluation pipeline.

        Args:
            measures: 所有安全措施 / All security measures.

        Returns:
            合并后的评估结果 / Merged evaluation result.
        """
        self._results.clear()

        if self.config.enable_access_control:
            self._check_access_control(measures)

        if self.config.enable_surveillance:
            self._check_surveillance(measures)

        if self.config.enable_baggage_screening:
            self._check_baggage_screening(measures)

        if self.config.enable_cost_objective:
            self._check_cost(measures)

        self._check_context()

        return self._merge_results()

    def _check_access_control(
        self,
        measures: tuple[SoftSecurityMeasure, ...],
    ) -> None:
        """校验访问控制 / Check access control.

        Args:
            measures: 安全措施 / Security measures.
        """
        _, result = self.access_constraint.evaluate(measures)
        self._results.append(result)

    def _check_surveillance(
        self,
        measures: tuple[SoftSecurityMeasure, ...],
    ) -> None:
        """校验监控覆盖 / Check surveillance coverage.

        Args:
            measures: 安全措施 / Security measures.
        """
        _, result = self.surveillance_constraint.evaluate(measures)
        self._results.append(result)

    def _check_baggage_screening(
        self,
        measures: tuple[SoftSecurityMeasure, ...],
    ) -> None:
        """校验行李安检 / Check baggage screening.

        Args:
            measures: 安全措施 / Security measures.
        """
        _, result = self.baggage_constraint.evaluate(measures)
        self._results.append(result)

    def _check_cost(
        self,
        measures: tuple[SoftSecurityMeasure, ...],
    ) -> None:
        """校验成本目标 / Check cost objective.

        Args:
            measures: 安全措施 / Security measures.
        """
        total, _ = self.cost_objective.compute(measures)
        gap = self.cost_objective.cost_gap(measures)
        if gap > 0.0:
            self._results.append(
                SoftSecurityResult.create_non_compliant(
                    score=0.5,
                    violations=(
                        f"cost_exceeded:{total:.2f}"
                        f">{self.cost_objective.target_cost:.2f}",
                    ),
                    total_cost=total,
                ),
            )
        else:
            self._results.append(
                SoftSecurityResult.create_compliant(
                    score=1.0,
                    total_cost=total,
                ),
            )

    def _check_context(self) -> None:
        """校验上下文基础项 / Check context basics."""
        ctx_result = self.context.validate()
        self._results.append(ctx_result)

    def _merge_results(self) -> SoftSecurityResult:
        """合并所有结果 / Merge all results.

        Returns:
            合并后的结果 / Merged result.
        """
        if not self._results:
            return SoftSecurityResult.create_compliant(score=1.0)

        merged = self._results[0]
        for r in self._results[1:]:
            merged = merged.merge(r)
        return merged

    def run_batch(
        self,
        *,
        measure_batches: tuple[tuple[SoftSecurityMeasure, ...], ...],
    ) -> SoftSecurityAggregation:
        """批量运行评估 / Run batch evaluation.

        Args:
            measure_batches: 多组安全措施 /
                Multiple sets of security measures.

        Returns:
            所有批次的聚合结果 / Aggregation of all batches.
        """
        from ...model.soft_security_aggregation import (
            SoftSecurityAggregation,
        )

        results: list[SoftSecurityResult] = []
        for batch in measure_batches:
            result = self.run(measures=batch)
            results.append(result)
        return SoftSecurityAggregation(results=tuple(results))
