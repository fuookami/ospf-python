"""CSP1D 长度分配模型。

管理长度分配优化模型的变量和约束。
Model for length assignment optimization.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.framework.csp1d.domain.length_assignment.model.length_assignment_modeling_config import (
    LengthAssignmentModelingConfig,
)


@dataclass(frozen=True)
class LengthAssignmentModel:
    """长度分配模型 / Length assignment model.

    管理长度分配问题中的决策变量、约束和目标。
    在列生成中负责将切割方案分配到具体长度。
    Manages decision variables, constraints, and
    objectives in the length assignment problem.
    Responsible for assigning cutting plans to
    specific lengths in column generation.

    Attributes:
        config: 建模配置。
            Modeling config.
        material_lengths: 可用材料长度集合。
            Set of available material lengths.
        product_lengths: 产品需求长度集合。
            Set of product demand lengths.
        assignments: 分配方案列表。
            List of assignment plans.
    """

    config: LengthAssignmentModelingConfig = field(
        default_factory=LengthAssignmentModelingConfig,
    )
    """建模配置 / Modeling config."""

    material_lengths: tuple[float, ...] = ()
    """可用材料长度 / Available material lengths."""

    product_lengths: tuple[float, ...] = ()
    """产品需求长度 / Product demand lengths."""

    assignments: tuple[tuple[str, float, int], ...] = ()
    """分配方案，格式 (产品键, 长度, 数量)。
    Assignment plans, format (product_key, length, quantity)."""

    @staticmethod
    def create(
        *,
        config: LengthAssignmentModelingConfig,
        material_lengths: tuple[float, ...],
        product_lengths: tuple[float, ...],
    ) -> LengthAssignmentModel:
        """创建长度分配模型。

        Create length assignment model.

        Args:
            config: 建模配置。
                Modeling config.
            material_lengths: 可用材料长度。
                Available material lengths.
            product_lengths: 产品需求长度。
                Product demand lengths.

        Returns:
            模型实例。
            Model instance.
        """
        return LengthAssignmentModel(
            config=config,
            material_lengths=material_lengths,
            product_lengths=product_lengths,
        )

    @property
    def material_count(self) -> int:
        """获取材料种类数。

        Get number of material types.

        Returns:
            材料种类数。
            Number of material types.
        """
        return len(self.material_lengths)

    @property
    def product_count(self) -> int:
        """获取产品种类数。

        Get number of product types.

        Returns:
            产品种类数。
            Number of product types.
        """
        return len(self.product_lengths)

    def with_assignments(
        self,
        *,
        assignments: tuple[tuple[str, float, int], ...],
    ) -> LengthAssignmentModel:
        """创建包含分配方案的新模型。

        Create new model with assignments.

        Args:
            assignments: 分配方案。
                Assignment plans.

        Returns:
            新模型实例。
            New model instance.
        """
        return LengthAssignmentModel(
            config=self.config,
            material_lengths=self.material_lengths,
            product_lengths=self.product_lengths,
            assignments=assignments,
        )
