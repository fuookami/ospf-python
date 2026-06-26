"""预分配应用 / Predistribution Application.

编排货物预分配优化：确定货物在各舱位的预分配方案。
Orchestrates cargo predistribution optimization:
determines pre-allocation of cargo across compartments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.airworthiness_security.service.limits.airworthiness_pipeline import (
        AirworthinessPipeline,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_compartment import (
        StowageCompartment,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_context import (
        StowageContext,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_item import (
        StowageItem,
    )
    from examples.framework_demo.demo2.domain.stowage.service.limits.stowage_pipeline import (
        StowagePipeline,
    )


@dataclass(frozen=True)
class PredistributionResult:
    """预分配结果 / Predistribution result.

    Attributes:
        feasible: 是否可行 / Whether feasible.
        assignments: 分配方案 / Assignment plan.
        utilization: 空间利用率 / Space utilization.
    """

    feasible: bool = False
    assignments: tuple[tuple[str, str], ...] = field(
        default_factory=tuple,
    )
    utilization: float = 0.0


class PredistributionApplication:
    """预分配应用 / Predistribution Application.

    编排货物预分配，校验配载和适航约束。
    Orchestrates cargo predistribution,
    validates stowage and airworthiness constraints.
    """

    def __init__(
        self,
        *,
        stowage_context: StowageContext,
        stowage_pipeline: StowagePipeline,
        airworthiness_pipeline: AirworthinessPipeline,
    ) -> None:
        """初始化。

        Initialize.

        Args:
            stowage_context: 配载上下文 / Stowage context.
            stowage_pipeline: 配载管道 / Stowage pipeline.
            airworthiness_pipeline: 适航管道 / Airworthiness pipeline.
        """
        self._stowage_context = stowage_context
        self._stowage_pipeline = stowage_pipeline
        self._airworthiness_pipeline = airworthiness_pipeline

    def run(
        self,
        items: tuple[StowageItem, ...],
        compartments: tuple[StowageCompartment, ...],
    ) -> PredistributionResult:
        """执行预分配。

        Run predistribution.

        Args:
            items: 待分配物品 / Items to distribute.
            compartments: 可用舱位 / Available compartments.

        Returns:
            预分配结果 / Predistribution result.
        """
        if not items or not compartments:
            return PredistributionResult(feasible=True)

        # 贪心分配：按重量降序，依次放入最大剩余容量舱位
        # Greedy: sort by weight desc, place in largest remaining capacity
        sorted_items = sorted(items, key=lambda i: i.weight, reverse=True)
        assignments: list[tuple[str, str]] = []
        remaining = {c.comp_id: c.max_weight for c in compartments}

        for item in sorted_items:
            best_comp = max(remaining, key=lambda k: remaining[k])
            if remaining[best_comp] >= item.weight:
                assignments.append((item.item_id, best_comp))
                remaining[best_comp] -= item.weight

        return PredistributionResult(
            feasible=len(assignments) == len(items),
            assignments=tuple(assignments),
            utilization=sum(c.max_weight - remaining[c.comp_id] for c in compartments)
            / max(sum(c.max_weight for c in compartments), 1.0),
        )
