"""CSP1D 长度分配上下文。

管理长度分配优化的入口与生命周期。
Context for length assignment optimization lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.framework.csp1d.domain.length_assignment.length_aggregation import (
    LengthAggregation,
)
from ospf_python.framework.csp1d.domain.length_assignment.model.length_assignment_modeling_config import (
    LengthAssignmentModelingConfig,
)
from ospf_python.framework.csp1d.domain.length_assignment.service.pipeline.length_constraint_pipeline import (
    LengthConstraintPipeline,
)
from ospf_python.framework.csp1d.domain.length_assignment.service.pipeline.length_objective_pipeline import (
    LengthObjectivePipeline,
)


@dataclass(frozen=True)
class LengthAssignmentContext:
    """长度分配上下文 / Length assignment context.

    管理长度分配优化的完整生命周期，包括注册
    材料和产品信息、执行约束和目标管线。
    Manages the full lifecycle of length assignment
    optimization, including registering material
    and product info, executing constraint and
    objective pipelines.

    Attributes:
        config: 建模配置。
            Modeling config.
        constraint_pipeline: 约束管线。
            Constraint pipeline.
        objective_pipeline: 目标管线。
            Objective pipeline.
    """

    config: LengthAssignmentModelingConfig = field(
        default_factory=LengthAssignmentModelingConfig,
    )
    """建模配置 / Modeling config."""

    constraint_pipeline: LengthConstraintPipeline = field(
        default_factory=LengthConstraintPipeline,
    )
    """约束管线 / Constraint pipeline."""

    objective_pipeline: LengthObjectivePipeline = field(
        default_factory=LengthObjectivePipeline,
    )
    """目标管线 / Objective pipeline."""

    def register(
        self,
        *,
        material_lengths: tuple[float, ...],
        product_lengths: tuple[float, ...],
    ) -> LengthAggregation:
        """注册材料和产品长度信息。

        Register material and product length info.

        Args:
            material_lengths: 可用材料长度。
                Available material lengths.
            product_lengths: 产品需求长度。
                Product demand lengths.

        Returns:
            长度分配聚合。
            Length assignment aggregation.
        """
        return LengthAggregation.create(
            config=self.config,
            material_lengths=material_lengths,
            product_lengths=product_lengths,
        )

    def apply_constraints(
        self,
        aggregation: LengthAggregation,
    ) -> LengthAggregation:
        """应用约束管线。

        Apply constraint pipeline.

        Args:
            aggregation: 当前聚合。
                Current aggregation.

        Returns:
            更新后的聚合。
            Updated aggregation.
        """
        return self.constraint_pipeline.apply(aggregation)

    def apply_objectives(
        self,
        aggregation: LengthAggregation,
    ) -> LengthAggregation:
        """应用目标管线。

        Apply objective pipeline.

        Args:
            aggregation: 当前聚合。
                Current aggregation.

        Returns:
            更新后的聚合。
            Updated aggregation.
        """
        return self.objective_pipeline.apply(aggregation)
