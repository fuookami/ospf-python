"""Generation selector for choosing the best strategy.

生成选择器：选择最佳策略。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..model.generation_context import GenerationContext
    from ..model.generation_result import GenerationResult
    from ..model.generation_strategy import GenerationStrategy


class GenerationSelector:
    """Selects the best generation strategy from registered options.

    从已注册选项中选择最佳生成策略。
    """

    def __init__(self, context: GenerationContext) -> None:
        self._context = context

    def select_best(
        self,
        tasks: tuple[Any, ...],
    ) -> GenerationResult | None:
        """Run all registered strategies and return the best result.

        运行所有已注册策略并返回最佳结果。
        """
        results: list[GenerationResult] = []
        for strategy in self._context.available_strategies():
            generator = self._context.get(strategy)
            if generator is not None:
                result = generator.generate(tasks)
                results.append(result)
        if not results:
            return None
        return max(results, key=lambda r: r.score)

    def evaluate_all(
        self,
        tasks: tuple[Any, ...],
    ) -> tuple[GenerationResult, ...]:
        """Run all strategies and return all results.

        运行所有策略并返回所有结果。
        """
        results: list[GenerationResult] = []
        for strategy in self._context.available_strategies():
            generator = self._context.get(strategy)
            if generator is not None:
                result = generator.generate(tasks)
                results.append(result)
        return tuple(results)

    def select_by_strategy(
        self,
        strategy: GenerationStrategy,
        tasks: tuple[Any, ...],
    ) -> GenerationResult | None:
        """Run a specific strategy and return its result.

        运行特定策略并返回其结果。
        """
        generator = self._context.get(strategy)
        if generator is None:
            return None
        result = generator.generate(tasks)
        return result  # type: ignore[no-any-return]

    @property
    def available_count(self) -> int:
        """Number of registered strategies.

        已注册策略数量。
        """
        return self._context.size
