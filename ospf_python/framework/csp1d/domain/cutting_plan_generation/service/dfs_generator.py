"""CSP1D DFS 切割方案生成器。

使用深度优先搜索枚举可行切割方案。
DFS-based cutting plan generator.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.generation_constraints import (
    GenerationConstraints,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_collector import (
    GenerationCollector,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_knife_pruning import (
    GenerationKnifePruning,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_length_pruning import (
    GenerationLengthPruning,
)


@dataclass(frozen=True)
class DfsGenerator:
    """DFS 切割方案生成器 / DFS cutting plan generator.

    通过深度优先搜索遍历产品组合空间，
    在搜索过程中使用刀数和长度剪枝策略
    以减少搜索量。
    Traverses product combination space via DFS,
    applying knife and length pruning strategies
    during search to reduce exploration.

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
        """生成所有可行切割方案。

        Generate all feasible cutting plans.

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
        knife_pruning = GenerationKnifePruning(
            max_knife_count=self.constraints.material_constraints.max_knife_count,
        )
        length_pruning = GenerationLengthPruning(
            material_length=material_length,
            min_waste_length=0.0,
            precision=self.constraints.material_constraints.precision,
        )
        current_plan: dict[str, int] = {}
        self._dfs(
            material_length=material_length,
            remaining_length=material_length,
            products=products,
            product_index=0,
            current_plan=current_plan,
            knife_pruning=knife_pruning,
            length_pruning=length_pruning,
            depth=0,
        )
        return self.collector.get_plans()

    def _dfs(
        self,
        *,
        material_length: float,
        remaining_length: float,
        products: list[tuple[str, float, int]],
        product_index: int,
        current_plan: dict[str, int],
        knife_pruning: GenerationKnifePruning,
        length_pruning: GenerationLengthPruning,
        depth: int,
    ) -> None:
        """递归 DFS 搜索。

        Recursive DFS search.

        Args:
            material_length: 原材料长度。
                Material length.
            remaining_length: 剩余长度。
                Remaining length.
            products: 产品列表。
                Product list.
            product_index: 当前产品索引。
                Current product index.
            current_plan: 当前方案。
                Current plan.
            knife_pruning: 刀数剪枝器。
                Knife pruner.
            length_pruning: 长度剪枝器。
                Length pruner.
            depth: 当前搜索深度。
                Current search depth.
        """
        if depth >= self.constraints.max_depth:
            self._try_collect(current_plan, remaining_length)
            return
        if self.collector.count >= self.constraints.max_solutions:
            return

        if product_index >= len(products):
            self._try_collect(current_plan, remaining_length)
            return

        product_key, product_length, max_qty = products[product_index]

        constraint = self.constraints.get_constraint_for(
            product_key,
        )
        min_qty = constraint.min_quantity if constraint else 0
        effective_max = min(
            max_qty,
            constraint.max_quantity if constraint else max_qty,
        )

        current_cuts = sum(current_plan.values())
        for qty in range(min_qty, effective_max + 1):
            needed = product_length * qty
            if qty > 0 and not length_pruning.can_fit_product(
                remaining_length,
                needed,
            ):
                break
            if qty > 0 and knife_pruning.should_prune(
                current_cuts + qty,
            ):
                break

            if qty > 0:
                current_plan[product_key] = qty
            elif product_key in current_plan:
                del current_plan[product_key]

            new_remaining = remaining_length - needed
            self._dfs(
                material_length=material_length,
                remaining_length=new_remaining,
                products=products,
                product_index=product_index + 1,
                current_plan=dict(current_plan),
                knife_pruning=knife_pruning,
                length_pruning=length_pruning,
                depth=depth + 1,
            )

        current_plan.pop(product_key, None)
        self._dfs(
            material_length=material_length,
            remaining_length=remaining_length,
            products=products,
            product_index=product_index + 1,
            current_plan=dict(current_plan),
            knife_pruning=knife_pruning,
            length_pruning=length_pruning,
            depth=depth + 1,
        )

    def _try_collect(
        self,
        plan: dict[str, int],
        remaining_length: float,
    ) -> None:
        """尝试收集非空方案。

        Try to collect non-empty plans.

        Args:
            plan: 当前方案。
                Current plan.
            remaining_length: 剩余长度。
                Remaining length.
        """
        if plan:
            self.collector.try_collect(dict(plan))
