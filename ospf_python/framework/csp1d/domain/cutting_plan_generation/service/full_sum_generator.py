"""CSP1D 全和生成器。

枚举所有可能的切割数量组合（穷举）。
Full-sum cutting plan generator (exhaustive).
"""

from __future__ import annotations

from operator import mul

from dataclasses import dataclass, field
from itertools import product as iter_product

from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.generation_constraints import (
    GenerationConstraints,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_collector import (
    GenerationCollector,
)
from ospf_python.utils.numeric import step_index


@dataclass(frozen=True)
class FullSumGenerator:
    """全和生成器 / Full sum generator.

    对所有产品的切割数量进行穷举组合，
    筛选出满足材料长度约束的可行方案。
    Exhaustively enumerates all quantity combinations
    for all products, filtering feasible plans that
    satisfy material length constraints.

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
        """穷举生成所有可行切割方案。

        Exhaustively generate all feasible cutting plans.

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

        quantity_ranges = []
        for product_key, product_length, max_qty in products:
            constraint = self.constraints.get_constraint_for(
                product_key,
            )
            min_qty = constraint.min_quantity if constraint else 0
            effective_max = min(
                max_qty,
                constraint.max_quantity if constraint else max_qty,
            )
            if product_length > 0:
                max_by_length = step_index(material_length / product_length)
                effective_max = min(
                    effective_max,
                    max_by_length,
                )
            quantity_ranges.append(
                range(min_qty, effective_max + 1),
            )

        # 把「产品键 / 产品长度」与长度一起提到循环外：内层每个组合都会用到它们，
        # 而原写法每轮都要 `range(len(products))`、反复索引 `products` 两次。
        # `sum(map(mul, combo, lengths))` 与 `sum(combo[i] * products[i][1] for i in ...)`
        # 逐位相同（同样的相乘与累加顺序，只是把索引换成了 C 级的 zip/map）。
        #
        # Hoist the keys/lengths out of the combo loop (the old body rebuilt
        # `range(len(products))` and indexed `products` twice per combo), and use
        # `sum(map(mul, ...))`, which is bit-identical to the indexed genexpr.
        keys = [product[0] for product in products]
        lengths = [product[1] for product in products]

        for combo in iter_product(*quantity_ranges):
            if self.collector.count >= self.constraints.max_solutions:
                break
            total_length = sum(map(mul, combo, lengths))
            if total_length <= material_length:
                plan = {
                    key: quantity
                    for key, quantity in zip(keys, combo)
                    if quantity > 0
                }
                if plan:
                    self.collector.try_collect(plan)

        return self.collector.get_plans()
