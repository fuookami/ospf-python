"""CSP2D 上下文 / CSP2D context.

CSP2D 框架的顶层上下文，聚合材料、产品和切割方案上下文。
Top-level context for the CSP2D framework, aggregating
material, product, and cutting plan contexts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.csp2d.domain.cutting_plan.cutting_plan_context import (
        CuttingPlanContext,
    )
    from ospf_python.framework.csp2d.domain.material.material_context import (
        MaterialContext,
    )
    from ospf_python.framework.csp2d.domain.product.product_context import (
        ProductContext,
    )


@dataclass(frozen=True)
class Csp2dContext:
    """CSP2D 上下文 / CSP2D context.

    聚合材料、产品和切割方案三个子上下文，提供统一访问入口。
    Aggregates material, product, and cutting plan sub-contexts,
    providing a unified access point.

    Attributes:
        material_context: 材料上下文 / Material context.
        product_context: 产品上下文 / Product context.
        cutting_plan_context: 切割方案上下文 / Cutting plan context.
    """

    material_context: MaterialContext
    """材料上下文 / Material context."""

    product_context: ProductContext
    """产品上下文 / Product context."""

    cutting_plan_context: CuttingPlanContext
    """切割方案上下文 / Cutting plan context."""

    @staticmethod
    def create(
        *,
        material_context: MaterialContext,
        product_context: ProductContext,
        cutting_plan_context: CuttingPlanContext,
    ) -> Csp2dContext:
        """创建 CSP2D 上下文 / Create CSP2D context.

        Args:
            material_context: 材料上下文 / Material context.
            product_context: 产品上下文 / Product context.
            cutting_plan_context: 切割方案上下文 /
                Cutting plan context.

        Returns:
            CSP2D 上下文实例 / Csp2dContext instance.
        """
        return Csp2dContext(
            material_context=material_context,
            product_context=product_context,
            cutting_plan_context=cutting_plan_context,
        )

    def clear(self) -> None:
        """清空所有子上下文 / Clear all sub-contexts.

        注意：因为 Csp2dContext 是 frozen dataclass，
        此方法无法直接修改内部状态。
        子上下文应各自实现 clear 方法。
        Note: Since Csp2dContext is a frozen dataclass,
        this method cannot directly modify internal state.
        Sub-contexts should implement their own clear methods.
        """
        self.material_context.clear()
        self.product_context.clear()
        self.cutting_plan_context.clear()
