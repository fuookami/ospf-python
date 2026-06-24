"""CSP1D 生产上下文 / CSP1D produce context."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ospf_python.framework.csp1d.domain.material.model.shadow_price_map import (
    ShadowPriceMap,
)

if TYPE_CHECKING:
    from ospf_python.framework.csp1d.application.model.csp1d_problem import (
        Csp1dProblem,
    )
    from ospf_python.framework.csp1d.domain.material.model.cutting_plan import (
        CuttingPlan,
    )


class Csp1dProduceContext:
    """生产建模上下文 / Production modeling context.

    管理切割方案池和影子价格，为列生成和 MILP 求解
    提供生产领域的建模入口。
    Manages the cutting plan pool and shadow prices,
    providing the production domain modeling entry point
    for column generation and MILP solving.

    Attributes:
        _problem: 问题定义 / Problem definition.
        _cutting_plans: 活跃切割方案池 / Active cutting plan pool.
        _shadow_prices: 影子价格映射 / Shadow price map.
    """

    def __init__(
        self,
        problem: Csp1dProblem,
    ) -> None:
        """初始化生产上下文 / Initialize produce context.

        Args:
            problem: 问题定义 / Problem definition.
        """
        self._problem = problem
        self._cutting_plans: list[CuttingPlan] = []
        self._shadow_prices = ShadowPriceMap()

    def add_cutting_plans(
        self,
        plans: tuple[CuttingPlan, ...],
    ) -> None:
        """添加切割方案 / Add cutting plans.

        Args:
            plans: 待添加的切割方案 / Plans to add.
        """
        self._cutting_plans.extend(plans)

    def remove_cutting_plans(
        self,
        indices: tuple[int, ...],
    ) -> None:
        """按索引移除切割方案 / Remove cutting plans by index.

        Args:
            indices: 待移除的索引 / Indices to remove.
        """
        index_set = frozenset(indices)
        self._cutting_plans = [
            p for i, p in enumerate(self._cutting_plans) if i not in index_set
        ]

    def update_shadow_prices(
        self,
        prices: ShadowPriceMap,
    ) -> None:
        """更新影子价格 / Update shadow prices.

        Args:
            prices: 新的影子价格 / New shadow prices.
        """
        self._shadow_prices = prices

    @property
    def problem(self) -> Csp1dProblem:
        """问题定义 / Problem definition."""
        return self._problem

    @property
    def cutting_plans(self) -> tuple[CuttingPlan, ...]:
        """活跃切割方案 / Active cutting plans."""
        return tuple(self._cutting_plans)

    @property
    def shadow_prices(self) -> ShadowPriceMap:
        """影子价格映射 / Shadow price map."""
        return self._shadow_prices
