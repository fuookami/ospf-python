"""CSP1D Top-K 切割方案选择 / CSP1D top-K cutting plan selection."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.csp1d.domain.material.model.cutting_plan import (
        CuttingPlan,
    )
    from ospf_python.framework.csp1d.domain.material.model.shadow_price_map import (
        ShadowPriceMap,
    )


class TopKCuttingPlans:
    """Top-K 切割方案选择器 / Top-K cutting plan selector.

    根据缩减成本（reduced cost）选择最优的 K 个切割方案。
    Selects the top-K cutting plans based on reduced cost.

    Attributes:
        _k: 选择数量 / Selection count.
    """

    def __init__(self, k: int) -> None:
        """初始化选择器 / Initialize selector.

        Args:
            k: 选择数量 / Selection count.
        """
        self._k = k

    def select(
        self,
        plans: tuple[CuttingPlan, ...],
        shadow_prices: ShadowPriceMap,
    ) -> tuple[CuttingPlan, ...]:
        """按缩减成本选择 Top-K 方案 / Select top-K plans by
        reduced cost.

        缩减成本 = 方案余料 - sum(产品影子价格 * 产品数量)。
        Reduced cost = plan waste - sum(product shadow price *
        product quantity).

        Args:
            plans: 候选切割方案 / Candidate cutting plans.
            shadow_prices: 影子价格映射 / Shadow price map.

        Returns:
            缩减成本最低的 Top-K 方案 / Top-K plans with lowest
            reduced cost.
        """
        scored: list[tuple[float, CuttingPlan]] = []
        for plan in plans:
            reduced_cost = plan.waste
            for product, qty in plan.products:
                reduced_cost -= shadow_prices.get(product.name) * qty
            scored.append((reduced_cost, plan))

        scored.sort(key=lambda x: x[0])
        return tuple(plan for _, plan in scored[: self._k])

    @property
    def k(self) -> int:
        """选择数量 / Selection count."""
        return self._k
