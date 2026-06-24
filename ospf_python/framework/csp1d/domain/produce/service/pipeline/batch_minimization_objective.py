"""CSP1D 批次最小化目标。

最小化生产批次数量以降低切换成本。
Batch minimization objective for production.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BatchMinimizationObjective:
    """批次最小化目标 / Batch minimization objective.

    最小化使用的生产批次数，以降低机器切换
    和调度复杂度。
    Minimizes the number of production batches
    used, reducing machine switching and
    scheduling complexity.

    Attributes:
        batch_penalty: 每批次惩罚系数。
            Penalty per batch.
        setup_penalty: 每次切换惩罚系数。
            Penalty per setup change.
    """

    batch_penalty: float = 1.0
    """批次惩罚 / Batch penalty."""

    setup_penalty: float = 0.5
    """切换惩罚 / Setup penalty."""

    def apply[T](self, aggregation: T) -> T:
        """应用批次最小化目标。

        Apply batch minimization objective.

        Args:
            aggregation: 生产聚合。
                Production aggregation.

        Returns:
            更新后的聚合。
            Updated aggregation.
        """
        return aggregation

    def compute_batch_cost(
        self,
        *,
        batch_count: int,
    ) -> float:
        """计算批次成本。

        Compute batch cost.

        Args:
            batch_count: 批次数。
                Batch count.

        Returns:
            批次成本。
            Batch cost.
        """
        return batch_count * self.batch_penalty

    def compute_setup_cost(
        self,
        *,
        setup_count: int,
    ) -> float:
        """计算切换成本。

        Compute setup cost.

        Args:
            setup_count: 切换次数。
                Setup count.

        Returns:
            切换成本。
            Setup cost.
        """
        return setup_count * self.setup_penalty

    def compute_total_cost(
        self,
        *,
        batch_count: int,
        setup_count: int,
    ) -> float:
        """计算总成本。

        Compute total cost.

        Args:
            batch_count: 批次数。
                Batch count.
            setup_count: 切换次数。
                Setup count.

        Returns:
            总成本。
            Total cost.
        """
        return self.compute_batch_cost(
            batch_count=batch_count
        ) + self.compute_setup_cost(setup_count=setup_count)
