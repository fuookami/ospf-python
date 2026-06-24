"""CSP1D N-求和生成器。

生成包含多种产品组合的切割方案。
Generator for multi-product cutting plans.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.generation_constraints import (
    GenerationConstraints,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_collector import (
    GenerationCollector,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_length_pruning import (
    GenerationLengthPruning,
)


@dataclass(frozen=True)
class NSumGenerator:
    """N-求和生成器 / N-sum generator.

    使用迭代加深方式生成多产品组合切割方案，
    每个方案包含至少两种不同产品。
    Generates multi-product cutting plans using
    iterative deepening. Each plan contains at
    least two different products.

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
        """生成多产品组合切割方案。

        Generate multi-product cutting plans.

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
        if len(products) < 2:
            return []

        length_pruning = GenerationLengthPruning(
            material_length=material_length,
            min_waste_length=0.0,
            precision=self.constraints.material_constraints.precision,
        )

        product_entries = []
        for product_key, product_length, max_qty in products:
            if product_length <= 0:
                continue
            constraint = self.constraints.get_constraint_for(
                product_key,
            )
            max_by_length = int(material_length / product_length)
            effective_max = min(max_qty, max_by_length)
            if constraint:
                effective_max = min(
                    effective_max,
                    constraint.max_quantity,
                )
            min_qty = constraint.min_quantity if constraint else 0
            product_entries.append(
                (product_key, product_length, min_qty, effective_max),
            )

        self._search(
            entries=product_entries,
            index=0,
            current_plan={},
            remaining_length=material_length,
            used_products=0,
            length_pruning=length_pruning,
        )
        return self.collector.get_plans()

    def _search(
        self,
        *,
        entries: list[tuple[str, float, int, int]],
        index: int,
        current_plan: dict[str, int],
        remaining_length: float,
        used_products: int,
        length_pruning: GenerationLengthPruning,
    ) -> None:
        """递归搜索多产品组合。

        Recursive search for multi-product combinations.

        Args:
            entries: 产品条目列表。
                Product entries list.
            index: 当前索引。
                Current index.
            current_plan: 当前方案。
                Current plan.
            remaining_length: 剩余长度。
                Remaining length.
            used_products: 已使用产品种类数。
                Number of product types used.
            length_pruning: 长度剪枝器。
                Length pruner.
        """
        if self.collector.count >= self.constraints.max_solutions:
            return

        if index >= len(entries):
            if used_products >= 2:
                self.collector.try_collect(dict(current_plan))
            return

        key, length, min_qty, max_qty = entries[index]

        for qty in range(min_qty, max_qty + 1):
            needed = length * qty
            if qty > 0 and not length_pruning.can_fit_product(
                remaining_length,
                needed,
            ):
                break
            if self.collector.count >= self.constraints.max_solutions:
                return

            if qty > 0:
                current_plan[key] = qty
                self._search(
                    entries=entries,
                    index=index + 1,
                    current_plan=current_plan,
                    remaining_length=remaining_length - needed,
                    used_products=used_products + 1,
                    length_pruning=length_pruning,
                )
                del current_plan[key]
            else:
                self._search(
                    entries=entries,
                    index=index + 1,
                    current_plan=current_plan,
                    remaining_length=remaining_length,
                    used_products=used_products,
                    length_pruning=length_pruning,
                )
