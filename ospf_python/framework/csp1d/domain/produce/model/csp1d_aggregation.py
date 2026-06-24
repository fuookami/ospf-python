"""CSP1D 生产聚合。

聚合生产领域的多个模型组件。
Aggregation for CSP1D production domain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.framework.csp1d.domain.produce.model.csp1d_model_context import (
    Csp1dModelContext,
)

if TYPE_CHECKING:
    from ospf_python.framework.csp1d.domain.produce.model.produce import (
        Produce,
    )


@dataclass(frozen=True)
class Csp1dAggregation:
    """CSP1D 生产聚合 / CSP1D production aggregation.

    聚合生产记录和模型上下文，协调领域内
    多个组件的注册和交互。
    Aggregates production records and model context,
    coordinating registration and interaction of
    multiple domain components.

    Attributes:
        context: 模型上下文。
            Model context.
        productions: 生产记录列表。
            Production records.
        batch_count: 批次数。
            Batch count.
    """

    context: Csp1dModelContext = field(
        default_factory=Csp1dModelContext,
    )
    """模型上下文 / Model context."""

    productions: tuple[Produce, ...] = ()
    """生产记录 / Production records."""

    batch_count: int = 0
    """批次数 / Batch count."""

    @staticmethod
    def create(
        *,
        context: Csp1dModelContext,
    ) -> Csp1dAggregation:
        """创建生产聚合。

        Create production aggregation.

        Args:
            context: 模型上下文。
                Model context.

        Returns:
            聚合实例。
            Aggregation instance.
        """
        return Csp1dAggregation(context=context)

    def with_productions(
        self,
        *,
        productions: tuple[Produce, ...],
    ) -> Csp1dAggregation:
        """创建包含生产记录的新聚合。

        Create new aggregation with productions.

        Args:
            productions: 生产记录。
                Production records.

        Returns:
            新聚合实例。
            New aggregation instance.
        """
        return Csp1dAggregation(
            context=self.context,
            productions=productions,
            batch_count=self.batch_count,
        )

    def with_batch_count(
        self,
        *,
        count: int,
    ) -> Csp1dAggregation:
        """创建更新批次数的新聚合。

        Create new aggregation with updated batch count.

        Args:
            count: 新批次数。
                New batch count.

        Returns:
            新聚合实例。
            New aggregation instance.
        """
        return Csp1dAggregation(
            context=self.context,
            productions=self.productions,
            batch_count=count,
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
