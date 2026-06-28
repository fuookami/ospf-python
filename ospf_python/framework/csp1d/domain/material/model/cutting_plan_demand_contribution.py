"""CSP1D 切割方案需求贡献。

记录切割方案对各产品需求的贡献情况。
Records how cutting plans contribute to product demands.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CuttingPlanDemandContribution:
    """切割方案需求贡献 / Cutting plan demand contribution.

    记录切割方案对各产品需求的贡献量，用于评估
    方案的有效性和需求满足进度。
    Records how cutting plans contribute to each
    product demand, used to evaluate plan effectiveness
    and demand fulfillment progress.

    Attributes:
        contributions: (产品键, 切割方案键, 贡献量) 元组。
            (product_key, plan_key, quantity) tuples.
        total_contributed: 总贡献量。
            Total contributed quantity.
    """

    contributions: tuple[tuple[str, str, int], ...] = ()
    """(产品键, 方案键, 贡献量) 元组 / (product, plan, qty) tuples."""

    total_contributed: int = 0
    """总贡献量 / Total contributed quantity."""

    @staticmethod
    def create(
        *,
        contributions: tuple[tuple[str, str, int], ...] = (),
    ) -> CuttingPlanDemandContribution:
        """创建需求贡献实例。

        Create demand contribution instance.

        Args:
            contributions: (产品键, 方案键, 贡献量) 元组。
                (product_key, plan_key, quantity) tuples.

        Returns:
            需求贡献实例。
            Demand contribution instance.
        """
        total = sum(qty for _, _, qty in contributions)
        return CuttingPlanDemandContribution(
            contributions=contributions,
            total_contributed=total,
        )

    def add(
        self,
        product_key: str,
        plan_key: str,
        quantity: int,
    ) -> CuttingPlanDemandContribution:
        """添加贡献记录，返回新实例。

        Add contribution record, return new instance.

        Args:
            product_key: 产品键。
                Product key.
            plan_key: 切割方案键。
                Cutting plan key.
            quantity: 贡献量。
                Contributed quantity.

        Returns:
            包含新贡献的实例。
            Instance with new contribution.
        """
        new_contributions = self.contributions + (
            (product_key, plan_key, quantity),
        )
        return CuttingPlanDemandContribution(
            contributions=new_contributions,
            total_contributed=self.total_contributed + quantity,
        )

    def contribution_for_product(
        self,
        product_key: str,
    ) -> int:
        """获取指定产品的总贡献量。

        Get total contribution for the specified product.

        Args:
            product_key: 产品键。
                Product key.

        Returns:
            该产品的贡献量总和，不存在返回 0。
            Sum of contributions for the product, 0 if none.
        """
        return sum(
            qty
            for prod, _, qty in self.contributions
            if prod == product_key
        )

    def contribution_for_plan(
        self,
        plan_key: str,
    ) -> int:
        """获取指定方案的总贡献量。

        Get total contribution for the specified plan.

        Args:
            plan_key: 切割方案键。
                Cutting plan key.

        Returns:
            该方案的贡献量总和，不存在返回 0。
            Sum of contributions for the plan, 0 if none.
        """
        return sum(
            qty
            for _, plan, qty in self.contributions
            if plan == plan_key
        )

    def product_keys(self) -> tuple[str, ...]:
        """获取所有涉及的产品键。

        Get all involved product keys.

        Returns:
            去重后的产品键元组。
            Deduplicated product key tuple.
        """
        seen: set[str] = set()
        result: list[str] = []
        for prod, _, _ in self.contributions:
            if prod not in seen:
                seen.add(prod)
                result.append(prod)
        return tuple(result)

    @property
    def has_contributions(self) -> bool:
        """判断是否有贡献记录。

        Check if there are contribution records.

        Returns:
            有贡献记录时返回 True。
            True when there are contribution records.
        """
        return len(self.contributions) > 0

    @property
    def unique_products(self) -> int:
        """获取涉及的产品种类数。

        Get number of distinct product types.

        Returns:
            去重后的产品种类数。
            Number of distinct product types.
        """
        return len(self.product_keys())
