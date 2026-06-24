"""CSP1D 余料最小化上下文。

管理余料最小化优化的入口与生命周期。
Context for waste minimization optimization lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.framework.csp1d.domain.wasting_minimization.service.pipeline.waste_objective_pipeline import (
    WasteObjectivePipeline,
)
from ospf_python.framework.csp1d.domain.wasting_minimization.waste_aggregation import (
    WasteAggregation,
)


@dataclass(frozen=True)
class WastingMinimizationContext:
    """余料最小化上下文 / Waste minimization context.

    管理余料最小化优化的完整生命周期，包括注册
    材料信息、应用目标管线和评估余料。
    Manages the full lifecycle of waste minimization
    optimization, including registering material info,
    applying objective pipeline, and evaluating waste.

    Attributes:
        target_waste_ratio: 目标余料率。
            Target waste ratio.
        objective_pipeline: 余料目标管线。
            Waste objective pipeline.
    """

    target_waste_ratio: float = 0.05
    """目标余料率 / Target waste ratio."""

    objective_pipeline: WasteObjectivePipeline = field(
        default_factory=WasteObjectivePipeline,
    )
    """余料目标管线 / Waste objective pipeline."""

    def register(
        self,
        *,
        material_lengths: tuple[float, ...],
    ) -> WasteAggregation:
        """注册材料长度信息。

        Register material length info.

        Args:
            material_lengths: 可用材料长度。
                Available material lengths.

        Returns:
            余料聚合。
            Waste aggregation.
        """
        return WasteAggregation.create(
            material_lengths=material_lengths,
            target_waste_ratio=self.target_waste_ratio,
        )

    def apply_objectives(
        self,
        aggregation: WasteAggregation,
    ) -> WasteAggregation:
        """应用余料目标管线。

        Apply waste objective pipeline.

        Args:
            aggregation: 当前聚合。
                Current aggregation.

        Returns:
            更新后的聚合。
            Updated aggregation.
        """
        return self.objective_pipeline.apply(aggregation)

    def evaluate_waste(
        self,
        *,
        aggregation: WasteAggregation,
        total_material_used: float,
        total_waste: float,
    ) -> WasteEvaluation:
        """评估余料状况。

        Evaluate waste situation.

        Args:
            aggregation: 余料聚合。
                Waste aggregation.
            total_material_used: 总材料使用量。
                Total material used.
            total_waste: 总余料量。
                Total waste.

        Returns:
            余料评估结果。
            Waste evaluation result.
        """
        if total_material_used <= 1e-8:
            ratio = 0.0
        else:
            ratio = total_waste / total_material_used
        is_below = aggregation.is_below_target(
            actual_ratio=ratio,
        )
        return WasteEvaluation(
            waste_ratio=ratio,
            is_below_target=is_below,
            total_waste=total_waste,
        )


@dataclass(frozen=True)
class WasteEvaluation:
    """余料评估结果 / Waste evaluation result.

    Attributes:
        waste_ratio: 余料率。
            Waste ratio.
        is_below_target: 是否低于目标。
            Whether below target.
        total_waste: 总余料量。
            Total waste.
    """

    waste_ratio: float = 0.0
    """余料率 / Waste ratio."""

    is_below_target: bool = False
    """低于目标 / Below target."""

    total_waste: float = 0.0
    """总余料 / Total waste."""
