"""CSP1D 领域策略。

定义 CSP1D 切割问题的领域约束策略。
Domain policy for CSP1D cutting stock problem.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Csp1dDomainPolicy:
    """CSP1D 领域策略 / CSP1D domain policy.

    定义 CSP1D 切割问题中的全局约束和配置策略，
    包括宽度容差、数量限制和余料阈值。
    Defines global constraints and configuration
    policies for the CSP1D cutting stock problem,
    including width tolerances, quantity limits,
    and waste thresholds.

    Attributes:
        width_tolerance: 宽度比较容差。
            Width comparison tolerance.
        min_waste_width: 最小余料宽度（低于此值视为零余料）。
            Minimum waste width (below this treated as zero).
        max_products_per_plan: 单个切割方案中的最大产品种类数。
            Maximum product types per cutting plan.
        max_quantity_per_product: 单个方案中每种产品的最大数量。
            Maximum quantity per product per plan.
        allow_zero_waste: 是否允许零余料方案。
            Whether to allow zero-waste plans.
    """

    width_tolerance: float = 1e-6
    """宽度比较容差 / Width comparison tolerance."""

    min_waste_width: float = 1e-8
    """最小余料宽度 / Minimum waste width."""

    max_products_per_plan: int = 100
    """单方案最大产品种类 / Max product types per plan."""

    max_quantity_per_product: int = 1000
    """单产品最大数量 / Max quantity per product."""

    allow_zero_waste: bool = True
    """允许零余料 / Allow zero waste."""

    @staticmethod
    def strict() -> Csp1dDomainPolicy:
        """创建严格策略。

        Create strict policy.

        使用更小的容差和更严格的限制。
        Uses smaller tolerances and stricter limits.

        Returns:
            严格策略实例。
            Strict policy instance.
        """
        return Csp1dDomainPolicy(
            width_tolerance=1e-9,
            min_waste_width=1e-10,
            max_products_per_plan=50,
            max_quantity_per_product=500,
            allow_zero_waste=True,
        )

    @staticmethod
    def relaxed() -> Csp1dDomainPolicy:
        """创建宽松策略。

        Create relaxed policy.

        使用更大的容差和更宽松的限制。
        Uses larger tolerances and relaxed limits.

        Returns:
            宽松策略实例。
            Relaxed policy instance.
        """
        return Csp1dDomainPolicy(
            width_tolerance=1e-4,
            min_waste_width=1e-6,
            max_products_per_plan=200,
            max_quantity_per_product=2000,
            allow_zero_waste=True,
        )

    def is_waste_zero(self, waste: float) -> bool:
        """判断余料是否视为零。

        Check if waste is considered zero.

        Args:
            waste: 余料宽度。
                Waste width.

        Returns:
            余料小于最小余料宽度时返回 True。
            True when waste is below minimum waste width.
        """
        return abs(waste) < self.min_waste_width

    def is_width_equal(self, lhs: float, rhs: float) -> bool:
        """判断两个宽度是否相等（在容差范围内）。

        Check if two widths are equal (within tolerance).

        Args:
            lhs: 左侧宽度。
                Left width.
            rhs: 右侧宽度。
                Right width.

        Returns:
            差值小于容差时返回 True。
            True when difference is within tolerance.
        """
        return abs(lhs - rhs) < self.width_tolerance

    def validate_quantity(self, quantity: int) -> bool:
        """验证产品数量是否在允许范围内。

        Check if product quantity is within allowed range.

        Args:
            quantity: 产品数量。
                Product quantity.

        Returns:
            数量在有效范围内返回 True。
            True when quantity is within valid range.
        """
        return 0 < quantity <= self.max_quantity_per_product

    def validate_product_count(self, count: int) -> bool:
        """验证产品种类数是否在允许范围内。

        Check if product type count is within allowed range.

        Args:
            count: 产品种类数。
                Product type count.

        Returns:
            种类数在有效范围内返回 True。
            True when count is within valid range.
        """
        return 0 < count <= self.max_products_per_plan
