"""束编组生成器 / Bunch generator.

根据物料项集合生成候选束编组方案。
Generates candidate bunch plans from material item sets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.bunch_generation.model.bunch_generation_context import (
        BunchGenerationContext,
    )


@dataclass(frozen=True)
class GeneratedBunch:
    """生成的束编组 / Generated bunch.

    Attributes:
        bunch_key: 束编组标识 / Bunch identifier.
        item_keys: 包含的物料项列表 / Contained item key list.
        score: 束编组评分 / Bunch score.
    """

    bunch_key: str
    item_keys: tuple[str, ...] = ()
    score: float = 0.0


@dataclass(frozen=True)
class GenerationResult:
    """生成结果 / Generation result.

    Attributes:
        context: 更新后的上下文 / Updated context.
        bunches: 生成的束编组列表 / Generated bunch list.
        is_complete: 是否完成 / Whether complete.
    """

    context: BunchGenerationContext
    bunches: tuple[GeneratedBunch, ...] = ()
    is_complete: bool = False


@dataclass(frozen=True)
class BunchGenerator:
    """束编组生成器 / Bunch generator.

    根据物料项集合和配置生成候选束编组方案。支持贪心策略
    和分组策略两种生成模式。
    Generates candidate bunch plans from material item sets
    and configuration. Supports greedy strategy and grouping
    strategy generation modes.

    Attributes:
        bunch_prefix: 束编组键前缀 / Bunch key prefix.
    """

    bunch_prefix: str = "gen"

    def generate_greedy(
        self,
        context: BunchGenerationContext,
    ) -> GenerationResult:
        """使用贪心策略生成束编组。

        Generate bunches using greedy strategy.

        按物料项顺序依次填充束编组，直到达到最大容量。
        Fills bunches sequentially by item order until max
        capacity is reached.

        Args:
            context: 生成上下文。/ Generation context.

        Returns:
            生成结果。/ Generation result.
        """
        if not context.item_keys:
            return GenerationResult(
                context=context.with_progress(1.0),
                is_complete=True,
            )

        max_size = context.config.max_bunch_size
        bunches: list[GeneratedBunch] = []
        current_items: list[str] = []
        bunch_idx = 0

        for item_key in context.item_keys:
            current_items.append(item_key)
            if len(current_items) >= max_size:
                bunches.append(
                    GeneratedBunch(
                        bunch_key=self._bunch_key(bunch_idx),
                        item_keys=tuple(current_items),
                    )
                )
                current_items = []
                bunch_idx += 1

        if current_items:
            bunches.append(
                GeneratedBunch(
                    bunch_key=self._bunch_key(bunch_idx),
                    item_keys=tuple(current_items),
                )
            )

        new_ctx = context.with_progress(1.0)
        for b in bunches:
            new_ctx = new_ctx.with_candidate(b.bunch_key)

        return GenerationResult(
            context=new_ctx,
            bunches=tuple(bunches),
            is_complete=True,
        )

    def generate_balanced(
        self,
        context: BunchGenerationContext,
        target_count: int,
    ) -> GenerationResult:
        """生成均衡束编组方案。

        Generate balanced bunch plan.

        将物料项均匀分配到指定数量的束编组中。
        Distributes items evenly across the specified number
        of bunches.

        Args:
            context: 生成上下文。/ Generation context.
            target_count: 目标束编组数 / Target bunch count.

        Returns:
            生成结果。/ Generation result.
        """
        if not context.item_keys or target_count <= 0:
            return GenerationResult(
                context=context.with_progress(1.0),
                is_complete=True,
            )

        items = list(context.item_keys)
        chunk_size = max(1, len(items) // target_count)
        bunches: list[GeneratedBunch] = []

        for i in range(target_count):
            start = i * chunk_size
            end = start + chunk_size if i < target_count - 1 else len(items)
            chunk = items[start:end]
            if chunk:
                bunches.append(
                    GeneratedBunch(
                        bunch_key=self._bunch_key(i),
                        item_keys=tuple(chunk),
                    )
                )

        new_ctx = context.with_progress(1.0)
        for b in bunches:
            new_ctx = new_ctx.with_candidate(b.bunch_key)

        return GenerationResult(
            context=new_ctx,
            bunches=tuple(bunches),
            is_complete=True,
        )

    def _bunch_key(self, index: int) -> str:
        """生成束编组键 / Generate bunch key.

        Args:
            index: 束编组索引。/ Bunch index.

        Returns:
            束编组键字符串。/ Bunch key string.
        """
        return f"{self.bunch_prefix}_{index}"
