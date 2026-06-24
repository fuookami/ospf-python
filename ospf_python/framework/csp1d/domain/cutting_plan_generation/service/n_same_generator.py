"""CSP1D N-相同生成器。

生成由同一种产品组成的切割方案。
Generator for cutting plans with identical products.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.generation_constraints import (
    GenerationConstraints,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_collector import (
    GenerationCollector,
)


@dataclass(frozen=True)
class NSameGenerator:
    """N-相同生成器 / N-same generator.

    为每种产品生成仅包含该产品的切割方案。
    每种产品根据材料长度计算最大可切割数量。
    Generates cutting plans with only one product type
    for each product. Calculates max cuttable quantity
    per product based on material length.

    Attributes:
        constraints: 生成约束集。
            Generation constraints.
        collector: 方案收集器。
            Plan collector.
    """

    constraints: GenerationConstraints = field(
        default_factory=GenerationConstraints,
    )
    """生成约束集 / Generation constraints."""

    collector: GenerationCollector = field(
        default_factory=GenerationCollector,
    )
    """方案收集器 / Plan collector."""

    def generate(
        self,
        *,
        material_length: float,
        products: list[tuple[str, float, int]],
    ) -> list[dict[str, int]]:
        """生成仅含单一产品的切割方案。

        Generate cutting plans with a single product type.

        Args:
            material_length: 原材料长度。
                Material length.
            products: 产品列表，每项为
                (产品键, 产品长度, 最大数量)。
                Product list, each item is
                (product_key, product_length, max_qty).

        Returns:
            可行切割方案列表。
            List of feasible cutting plans.
        """
        if not products:
            return []

        for product_key, product_length, max_qty in products:
            if product_length <= 0:
                continue
            max_by_length = int(material_length / product_length)
            effective_max = min(max_qty, max_by_length)

            constraint = self.constraints.get_constraint_for(
                product_key,
            )
            min_qty = constraint.min_quantity if constraint else 1
            min_qty = max(min_qty, 1)
            effective_max = min(
                effective_max,
                constraint.max_quantity if constraint else effective_max,
            )

            for qty in range(min_qty, effective_max + 1):
                if self.collector.count >= self.constraints.max_solutions:
                    return self.collector.get_plans()
                plan = {product_key: qty}
                self.collector.try_collect(plan)

        return self.collector.get_plans()
