"""Bunch generation pipeline composing all strategies.

任务组生成管道：组合所有策略。
"""

from __future__ import annotations

from typing import Any

from ..model.generation_aggregation import (
    GenerationAggregation,
)
from ..model.generation_config import GenerationConfig
from ..model.generation_context import GenerationContext
from .generation_selector import GenerationSelector


class BunchGenerationPipeline:
    """Orchestrates bunch generation across strategies.

    协调跨策略的任务组生成。
    """

    def __init__(self) -> None:
        self._context = GenerationContext()
        self._config = GenerationConfig()
        self._selector = GenerationSelector(self._context)

    def configure(self, config: GenerationConfig) -> None:
        """Set the generation configuration.

        设置生成配置。
        """
        self._config = config
        self._selector = GenerationSelector(self._context)

    def register_strategy(
        self,
        strategy: Any,
        generator: Any,
    ) -> None:
        """Register a generation strategy.

        注册生成策略。
        """
        self._context.register(strategy, generator)
        self._selector = GenerationSelector(self._context)

    def execute(
        self,
        tasks: tuple[Any, ...],
    ) -> GenerationAggregation:
        """Run all strategies and aggregate results.

        运行所有策略并聚合结果。
        """
        results = self._selector.evaluate_all(tasks)
        return GenerationAggregation.from_results(results)

    @property
    def config(self) -> GenerationConfig:
        """Access the current configuration.

        访问当前配置。
        """
        return self._config

    @property
    def context(self) -> GenerationContext:
        """Access the generation context.

        访问生成上下文。
        """
        return self._context

    @property
    def selector(self) -> GenerationSelector:
        """Access the generation selector.

        访问生成选择器。
        """
        return self._selector
