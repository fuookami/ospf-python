"""CSP1D 产出率目标管线。

向产出率模型添加最大化产出率的目标。
Yield objective pipeline for yield optimization.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class YieldObjectivePipeline:
    """产出率目标管线 / Yield objective pipeline.

    在产出率模型中添加最大化产出率的目标函数。
    在列生成中用于评估切割方案的产出率贡献。
    Adds yield maximization objective to the yield
    model. Used in column generation to evaluate
    yield contribution of cutting plans.

    Attributes:
        yield_weight: 产出率奖励权重。
            Yield reward weight.
        shortfall_penalty: 产出率缺口惩罚。
            Yield shortfall penalty.
    """

    yield_weight: float = 1.0
    """产出率奖励权重 / Yield reward weight."""

    shortfall_penalty: float = 10.0
    """缺口惩罚 / Shortfall penalty."""

    def apply[T](self, aggregation: T) -> T:
        """应用产出率目标。

        Apply yield objective.

        Args:
            aggregation: 产出率聚合。
                Yield aggregation.

        Returns:
            更新后的聚合。
            Updated aggregation.
        """
        return aggregation

    def compute_yield_reward(
        self,
        *,
        yield_ratio: float,
    ) -> float:
        """计算产出率奖励。

        Compute yield reward.

        Args:
            yield_ratio: 产出率。
                Yield ratio.

        Returns:
            产出率奖励（负值表示减少成本）。
            Yield reward (negative means cost reduction).
        """
        return -yield_ratio * self.yield_weight

    def compute_shortfall_penalty(
        self,
        *,
        actual_ratio: float,
        target_ratio: float,
    ) -> float:
        """计算产出率缺口惩罚。

        Compute yield shortfall penalty.

        Args:
            actual_ratio: 实际产出率。
                Actual yield ratio.
            target_ratio: 目标产出率。
                Target yield ratio.

        Returns:
            缺口惩罚成本。
            Shortfall penalty cost.
        """
        shortfall = max(0.0, target_ratio - actual_ratio)
        return shortfall * self.shortfall_penalty

    def compute_reduced_cost(
        self,
        *,
        yield_ratio: float,
        target_ratio: float,
        shadow_price: float,
    ) -> float:
        """计算切割方案的 reduced cost。

        Compute reduced cost of a cutting plan.

        Args:
            yield_ratio: 产出率。
                Yield ratio.
            target_ratio: 目标产出率。
                Target yield ratio.
            shadow_price: 影子价格。
                Shadow price.

        Returns:
            reduced cost 值。
            Reduced cost value.
        """
        return (
            self.compute_yield_reward(
                yield_ratio=yield_ratio,
            )
            + self.compute_shortfall_penalty(
                actual_ratio=yield_ratio,
                target_ratio=target_ratio,
            )
            - shadow_price
        )
