"""重量均衡评估管道 / Weight equalization evaluation pipeline.

组合所有均衡约束和目标为统一验证管道。
Composes all equalization constraints and objectives
into a unified validation pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ...model.equalization_result import EqualizationResult

if TYPE_CHECKING:
    from ...model.equalization_aggregation import (
        EqualizationAggregation,
    )
    from ...model.equalization_context import EqualizationContext
    from .equalization_objective import EqualizationObjective
    from .lateral_balance_constraint import (
        LateralBalanceConstraint,
        LateralCompartmentWeight,
    )
    from .longitudinal_balance_constraint import (
        LongitudinalBalanceConstraint,
        LongitudinalCompartmentWeight,
    )


@dataclass(frozen=True)
class EqualizationPipelineConfig:
    """均衡管道配置 / Pipeline configuration.

    控制管道中启用哪些约束和目标。
    Controls which constraints and objectives are enabled.

    Attributes:
        enable_lateral: 启用横向约束 /
            Enable lateral constraint.
        enable_longitudinal: 启用纵向约束 /
            Enable longitudinal constraint.
        enable_objective: 启用均衡优化目标 /
            Enable equalization objective.
    """

    enable_lateral: bool = True
    enable_longitudinal: bool = True
    enable_objective: bool = True


@dataclass
class EqualizationPipeline:
    """重量均衡评估管道 / Equalization evaluation pipeline.

    按顺序执行横向平衡、纵向平衡约束检查，加上均衡
    优化目标，合并结果返回。
    Executes lateral and longitudinal balance constraint
    checks in sequence, plus the equalization objective,
    merging results for return.

    Attributes:
        context: 均衡上下文 / Equalization context.
        lateral_constraint: 横向约束 / Lateral constraint.
        longitudinal_constraint: 纵向约束 /
            Longitudinal constraint.
        objective: 均衡目标 / Equalization objective.
        config: 管道配置 / Pipeline configuration.
        _results: 内部结果收集 / Internal result collection.
    """

    context: EqualizationContext
    lateral_constraint: LateralBalanceConstraint
    longitudinal_constraint: LongitudinalBalanceConstraint
    objective: EqualizationObjective
    config: EqualizationPipelineConfig = field(
        default_factory=EqualizationPipelineConfig,
    )
    _results: list[EqualizationResult] = field(
        default_factory=list,
        init=False,
    )

    def run_lateral(
        self,
        *,
        weights: tuple[LateralCompartmentWeight, ...],
    ) -> None:
        """运行横向平衡检查 / Run lateral balance check.

        Args:
            weights: 横向舱室重量 / Lateral compartment weights.
        """
        _, result = self.lateral_constraint.evaluate(weights)
        self._results.append(result)

    def run_longitudinal(
        self,
        *,
        weights: tuple[LongitudinalCompartmentWeight, ...],
    ) -> None:
        """运行纵向平衡检查 / Run longitudinal balance check.

        Args:
            weights: 纵向舱室重量 /
                Longitudinal compartment weights.
        """
        _, result = self.longitudinal_constraint.evaluate(weights)
        self._results.append(result)

    def run(
        self,
        *,
        lateral_weights: tuple[LateralCompartmentWeight, ...],
        longitudinal_weights: tuple[LongitudinalCompartmentWeight, ...],
    ) -> EqualizationResult:
        """运行完整均衡评估管道。

        Run the full equalization evaluation pipeline.

        Args:
            lateral_weights: 横向舱室重量 /
                Lateral compartment weights.
            longitudinal_weights: 纵向舱室重量 /
                Longitudinal compartment weights.

        Returns:
            合并后的评估结果 / Merged evaluation result.
        """
        self._results.clear()

        if self.config.enable_lateral:
            self.run_lateral(weights=lateral_weights)

        if self.config.enable_longitudinal:
            self.run_longitudinal(weights=longitudinal_weights)

        self._check_context()

        return self._merge_results()

    def _check_context(self) -> None:
        """校验上下文基础项 / Check context basics."""
        ctx_result = self.context.validate()
        self._results.append(ctx_result)

    def _merge_results(self) -> EqualizationResult:
        """合并所有结果 / Merge all results.

        Returns:
            合并后的结果 / Merged result.
        """
        if not self._results:
            return EqualizationResult.create_balanced(
                max_imbalance=0.0,
            )

        merged = self._results[0]
        for r in self._results[1:]:
            merged = merged.merge(r)
        return merged

    def run_multi_axis(
        self,
        *,
        lateral_batches: tuple[tuple[LateralCompartmentWeight, ...], ...],
        longitudinal_batches: tuple[tuple[LongitudinalCompartmentWeight, ...], ...],
    ) -> EqualizationAggregation:
        """多轴批量运行 / Run multi-axis batch evaluation.

        Args:
            lateral_batches: 多组横向重量 /
                Multiple sets of lateral weights.
            longitudinal_batches: 多组纵向重量 /
                Multiple sets of longitudinal weights.

        Returns:
            所有批次的聚合结果 / Aggregation of all batches.
        """
        from ...model.equalization_aggregation import (
            EqualizationAggregation,
        )

        results: list[EqualizationResult] = []
        max_batches = max(
            len(lateral_batches),
            len(longitudinal_batches),
        )
        for i in range(max_batches):
            lat = lateral_batches[i] if i < len(lateral_batches) else ()
            lon = longitudinal_batches[i] if i < len(longitudinal_batches) else ()
            result = self.run(
                lateral_weights=lat,
                longitudinal_weights=lon,
            )
            results.append(result)
        return EqualizationAggregation(
            results=tuple(results),
        )
