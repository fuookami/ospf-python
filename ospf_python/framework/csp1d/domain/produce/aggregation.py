"""CSP1D 生产聚合。

组合生产领域的多个模型组件。
Produce aggregation combining domain components.
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
    from ospf_python.framework.csp1d.domain.produce.model.produce import (
        Produce,
    )


@dataclass(frozen=True)
class Aggregation:
    """生产聚合 / Produce aggregation.

    组合 CSP1D 生产聚合与生产记录，提供统一
    的领域聚合入口。
    Combines CSP1D production aggregation and
    production records, providing a unified
    domain aggregation entry point.

    Attributes:
        csp1d: CSP1D 生产聚合。
            CSP1D production aggregation.
        productions: 生产记录列表。
            Production records.
    """

    csp1d: Csp1dAggregation = field(
        default_factory=Csp1dAggregation,
    )
    """CSP1D 生产聚合 / CSP1D aggregation."""

    productions: tuple[Produce, ...] = ()
    """生产记录 / Production records."""

    @staticmethod
    def create(
        *,
        context: Csp1dModelContext,
    ) -> Aggregation:
        """创建生产聚合。

        Create produce aggregation.

        Args:
            context: 模型上下文。
                Model context.

        Returns:
            聚合实例。
            Aggregation instance.
        """
        csp1d = Csp1dAggregation.create(context=context)
        return Aggregation(csp1d=csp1d)

    def with_productions(
        self,
        *,
        productions: tuple[Produce, ...],
    ) -> Aggregation:
        """创建包含生产记录的新聚合。

        Create new aggregation with productions.

        Args:
            productions: 生产记录。
                Production records.

        Returns:
            新聚合实例。
            New aggregation instance.
        """
        return Aggregation(
            csp1d=self.csp1d,
            productions=productions,
        )

    @property
    def total_quantity(self) -> int:
        """获取总生产数量。

        Get total production quantity.

        Returns:
            所有生产记录的数量之和。
            Sum of all production quantities.
        """
        return sum(p.quantity for p in self.productions)

    @property
    def product_count(self) -> int:
        """获取产品种类数。

        Get number of product types.

        Returns:
            不同产品种类的数量。
            Number of distinct product types.
        """
        return len({p.product_key for p in self.productions})
