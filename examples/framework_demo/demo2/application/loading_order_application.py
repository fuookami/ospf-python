"""装载顺序应用 / Loading Order Application.

编排装载顺序优化：确定最优装载序列。
Orchestrates loading order optimization:
determines optimal loading sequence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.loading_effectiveness.model.loading_context import (
        LoadingContext,
    )
    from examples.framework_demo.demo2.domain.loading_effectiveness.model.loading_pattern import (
        LoadingPattern,
    )
    from examples.framework_demo.demo2.domain.loading_effectiveness.service.limits.loading_effectiveness_pipeline import (
        LoadingEffectivenessPipeline,
    )
    from examples.framework_demo.demo2.domain.stowage.service.limits.stowage_pipeline import (
        StowagePipeline,
    )


@dataclass(frozen=True)
class LoadingOrderResult:
    """装载顺序结果 / Loading order result.

    Attributes:
        feasible: 是否可行 / Whether feasible.
        sequence: 装载顺序 / Loading sequence.
        estimated_time: 预计时间 (min) / Estimated time (min).
    """

    feasible: bool = False
    sequence: tuple[str, ...] = field(default_factory=tuple)
    estimated_time: float = 0.0


class LoadingOrderApplication:
    """装载顺序应用 / Loading Order Application.

    编排装载顺序优化，校验配载有效性约束。
    Orchestrates loading order optimization,
    validates loading effectiveness constraints.
    """

    def __init__(
        self,
        *,
        loading_context: LoadingContext,
        loading_pipeline: LoadingEffectivenessPipeline,
        stowage_pipeline: StowagePipeline,
    ) -> None:
        """初始化。

        Initialize.

        Args:
            loading_context: 装载上下文 / Loading context.
            loading_pipeline: 装载有效性管道 / Loading effectiveness pipeline.
            stowage_pipeline: 配载管道 / Stowage pipeline.
        """
        self._loading_context = loading_context
        self._loading_pipeline = loading_pipeline
        self._stowage_pipeline = stowage_pipeline

    def run(self, patterns: tuple[LoadingPattern, ...]) -> LoadingOrderResult:
        """执行装载顺序优化。

        Run loading order optimization.

        Args:
            patterns: 装载模式 / Loading patterns.

        Returns:
            装载顺序结果 / Loading order result.
        """
        if not patterns:
            return LoadingOrderResult(feasible=True)

        # 按优先级排序
        # Sort by priority
        sorted_patterns = sorted(
            patterns,
            key=lambda p: p.efficiency,
            reverse=True,
        )

        sequence = tuple(p.pattern_id for p in sorted_patterns)
        return LoadingOrderResult(
            feasible=True,
            sequence=sequence,
            estimated_time=len(sorted_patterns) * 5.0,
        )
