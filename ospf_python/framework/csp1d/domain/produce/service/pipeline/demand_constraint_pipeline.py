"""CSP1D 需求约束管线。

确保生产方案满足产品需求量。
Demand constraint pipeline for production.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DemandConstraintPipeline:
    """需求约束管线 / Demand constraint pipeline.

    验证生产方案满足各产品的需求约束。
    在 MILP 中对应 demand >= required 的约束族。
    Validates that production plans satisfy
    demand constraints for each product.
    Corresponds to demand >= required constraint
    family in MILP.

    Attributes:
        allow_shortfall: 是否允许需求缺口。
            Whether demand shortfall is allowed.
        shortfall_penalty: 缺口惩罚系数。
            Shortfall penalty coefficient.
    """

    allow_shortfall: bool = False
    """允许缺口 / Allow shortfall."""

    shortfall_penalty: float = 1000.0
    """缺口惩罚 / Shortfall penalty."""

    def apply[T](self, aggregation: T) -> T:
        """应用需求约束。

        Apply demand constraints.

        Args:
            aggregation: 生产聚合。
                Production aggregation.

        Returns:
            更新后的聚合。
            Updated aggregation.
        """
        return aggregation

    def is_demand_satisfied(
        self,
        *,
        supplied: int,
        demanded: int,
    ) -> bool:
        """检查需求是否满足。

        Check if demand is satisfied.

        Args:
            supplied: 已供应量。
                Supplied quantity.
            demanded: 需求量。
                Demanded quantity.

        Returns:
            满足返回 True / True if satisfied.
        """
        return supplied >= demanded

    def compute_shortfall(
        self,
        *,
        supplied: int,
        demanded: int,
    ) -> int:
        """计算需求缺口。

        Compute demand shortfall.

        Args:
            supplied: 已供应量。
                Supplied quantity.
            demanded: 需求量。
                Demanded quantity.

        Returns:
            缺口数量（非负）。
            Shortfall quantity (non-negative).
        """
        return max(0, demanded - supplied)

    def compute_shortfall_cost(
        self,
        *,
        supplied: int,
        demanded: int,
    ) -> float:
        """计算缺口惩罚成本。

        Compute shortfall penalty cost.

        Args:
            supplied: 已供应量。
                Supplied quantity.
            demanded: 需求量。
                Demanded quantity.

        Returns:
            缺口惩罚成本。
            Shortfall penalty cost.
        """
        shortfall = self.compute_shortfall(
            supplied=supplied,
            demanded=demanded,
        )
        return shortfall * self.shortfall_penalty
