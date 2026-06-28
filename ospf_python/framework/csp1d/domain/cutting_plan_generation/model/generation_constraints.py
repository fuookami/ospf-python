"""CSP1D 切割方案生成约束集。

汇总切割方案生成过程中的所有约束。
Generation constraints for cutting plan generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.constraints import (
    Constraints,
)

if TYPE_CHECKING:
    from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.cutting_plan_constraint import (
        CuttingPlanConstraint,
    )


@dataclass(frozen=True)
class GenerationConstraints:
    """切割方案生成约束集 / Generation constraints.

    汇总生成过程中涉及的材料约束和产品约束，
    用于指导 DFS/穷举等生成算法。
    Aggregates material and product constraints
    during generation to guide DFS/exhaustive algorithms.

    Attributes:
        material_constraints: 材料级约束。
            Material-level constraints.
        product_constraints: 产品级约束列表。
            List of product-level constraints.
        max_depth: 最大搜索深度。
            Maximum search depth.
        max_solutions: 最大解数量。
            Maximum number of solutions.
    """

    material_constraints: Constraints = field(
        default_factory=Constraints,
    )
    """材料级约束 / Material-level constraints."""

    product_constraints: tuple[CuttingPlanConstraint, ...] = ()
    """产品级约束列表 / Product-level constraints."""

    max_depth: int = 100
    """最大搜索深度 / Maximum search depth."""

    max_solutions: int = 10000
    """最大解数量 / Maximum number of solutions."""

    @staticmethod
    def create(
        *,
        material_constraints: Constraints,
        product_constraints: tuple[CuttingPlanConstraint, ...],
        max_depth: int = 100,
        max_solutions: int = 10000,
    ) -> GenerationConstraints:
        """创建生成约束集。

        Create generation constraints.

        Args:
            material_constraints: 材料级约束。
                Material-level constraints.
            product_constraints: 产品级约束。
                Product-level constraints.
            max_depth: 最大搜索深度，默认 100。
                Maximum search depth, default 100.
            max_solutions: 最大解数量，默认 10000。
                Maximum solutions, default 10000.

        Returns:
            生成约束集实例。
            GenerationConstraints instance.
        """
        return GenerationConstraints(
            material_constraints=material_constraints,
            product_constraints=product_constraints,
            max_depth=max_depth,
            max_solutions=max_solutions,
        )

    @property
    def active_product_count(self) -> int:
        """获取活跃产品约束数量。

        Get count of active product constraints.

        Returns:
            活跃约束数量。
            Number of active constraints.
        """
        return sum(1 for c in self.product_constraints if c.is_active)

    def get_constraint_for(
        self,
        product_key: str,
    ) -> CuttingPlanConstraint | None:
        """获取指定产品的约束。

        Get constraint for the specified product.

        Args:
            product_key: 产品键 / Product key.

        Returns:
            产品约束或 None。
            Product constraint or None.
        """
        return next(
            (c for c in self.product_constraints if c.product_key == product_key),
            None,
        )
