"""CSP1D 生产层聚合。

组合生产领域的聚合组件。
Produce-level aggregation combining domain components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.framework.csp1d.domain.produce.model.csp1d_aggregation import (
    Csp1dAggregation,
)

if TYPE_CHECKING:
    from ospf_python.framework.csp1d.domain.produce.model.csp1d_model_context import (
        Csp1dModelContext,
    )


@dataclass(frozen=True)
class ProduceAggregation:
    """生产层聚合 / Produce aggregation.

    组合 CSP1D 生产聚合并提供统一的领域入口。
    Combines CSP1D production aggregation and
    provides a unified domain entry point.

    Attributes:
        csp1d: CSP1D 生产聚合。
            CSP1D production aggregation.
        max_batches: 最大批次数。
            Maximum batch count.
    """

    csp1d: Csp1dAggregation = field(
        default_factory=Csp1dAggregation,
    )
    """CSP1D 生产聚合 / CSP1D aggregation."""

    max_batches: int = 1000
    """最大批次数 / Maximum batch count."""

    @staticmethod
    def create(
        *,
        context: Csp1dModelContext,
        max_batches: int = 1000,
    ) -> ProduceAggregation:
        """创建生产层聚合。

        Create produce aggregation.

        Args:
            context: 模型上下文。
                Model context.
            max_batches: 最大批次数，默认 1000。
                Maximum batch count, default 1000.

        Returns:
            聚合实例。
            Aggregation instance.
        """
        csp1d = Csp1dAggregation.create(context=context)
        return ProduceAggregation(
            csp1d=csp1d,
            max_batches=max_batches,
        )

    @property
    def total_quantity(self) -> int:
        """获取总生产数量。

        Get total production quantity.

        Returns:
            总生产数量。
            Total production quantity.
        """
        return self.csp1d.total_quantity

    @property
    def product_count(self) -> int:
        """获取产品种类数。

        Get number of product types.

        Returns:
            产品种类数。
            Number of product types.
        """
        return self.csp1d.product_count
