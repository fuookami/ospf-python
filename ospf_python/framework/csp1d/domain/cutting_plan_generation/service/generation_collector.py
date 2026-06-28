"""CSP1D 切割方案收集器。

收集并去重生成的切割方案。
Collector for generated cutting plans with deduplication.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.cutting_plan_canonical_key import (
    CuttingPlanCanonicalKey,
)


@dataclass
class GenerationCollector:
    """切割方案收集器 / Cutting plan collector.

    收集生成算法产出的切割方案，自动去重。
    Collects cutting plans produced by generation
    algorithms with automatic deduplication.

    Attributes:
        collected: 已收集的方案列表（键 -> 数量映射）。
            List of collected plans (key -> quantity mapping).
        seen_keys: 已见过的规范键集合。
            Set of seen canonical keys.
    """

    collected: list[dict[str, int]] = field(
        default_factory=list,
    )
    """已收集的方案列表 / Collected plans."""

    seen_keys: set[CuttingPlanCanonicalKey] = field(
        default_factory=set,
    )
    """已见过的规范键 / Seen canonical keys."""

    def try_collect(
        self,
        plan: dict[str, int],
    ) -> bool:
        """尝试收集一条切割方案。

        Try to collect a cutting plan.

        如果方案的规范键已存在则跳过。
        Skips if the plan's canonical key already exists.

        Args:
            plan: 产品键到数量的映射。
                Product key to quantity mapping.

        Returns:
            成功收集返回 True / True if successfully collected.
        """
        key = CuttingPlanCanonicalKey.create(items=plan)
        if key in self.seen_keys:
            return False
        self.seen_keys.add(key)
        self.collected.append(plan)
        collected = True
        return collected

    def collect_all(
        self,
        plans: list[dict[str, int]],
    ) -> int:
        """批量收集切割方案。

        Batch collect cutting plans.

        Args:
            plans: 切割方案列表。
                List of cutting plans.

        Returns:
            成功收集的数量。
            Number of successfully collected plans.
        """
        count = 0
        for plan in plans:
            if self.try_collect(plan):
                count += 1
        return count

    @property
    def count(self) -> int:
        """获取已收集方案数量。

        Get count of collected plans.

        Returns:
            方案数量。
            Number of plans.
        """
        return len(self.collected)

    @property
    def is_empty(self) -> bool:
        """判断是否为空。

        Check if collector is empty.

        Returns:
            无方案时返回 True / True if no plans.
        """
        return len(self.collected) == 0

    def get_plans(self) -> list[dict[str, int]]:
        """获取所有已收集的方案。

        Get all collected plans.

        Returns:
            方案列表的副本。
            Copy of the plans list.
        """
        return list(self.collected)

    def clear(self) -> None:
        """清空收集器。

        Clear the collector.
        """
        self.collected.clear()
        self.seen_keys.clear()
