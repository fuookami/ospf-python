"""Generation context for managing strategy registry.

生成上下文：管理策略注册表。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .generation_strategy import GenerationStrategy


class GenerationContext:
    """Registry mapping strategies to their generator implementations.

    将策略映射到其生成器实现的注册表。
    """

    def __init__(self) -> None:
        self._registry: dict[GenerationStrategy, Any] = {}

    def register(
        self,
        strategy: GenerationStrategy,
        generator: Any,
    ) -> None:
        """Register a generator for a strategy.

        为策略注册生成器。
        """
        self._registry[strategy] = generator

    def get(
        self,
        strategy: GenerationStrategy,
    ) -> Any | None:
        """Retrieve the generator for a strategy.

        检索策略的生成器。
        """
        return self._registry.get(strategy)

    def available_strategies(self) -> tuple[GenerationStrategy, ...]:
        """List all registered strategies.

        列出所有已注册的策略。
        """
        return tuple(self._registry.keys())

    def is_registered(
        self,
        strategy: GenerationStrategy,
    ) -> bool:
        """Check whether a strategy has a registered generator.

        检查策略是否有已注册的生成器。
        """
        return strategy in self._registry

    def unregister(
        self,
        strategy: GenerationStrategy,
    ) -> bool:
        """Remove a strategy registration. Returns True if found.

        移除策略注册。找到则返回 True。
        """
        if strategy in self._registry:
            del self._registry[strategy]
            return True
        return False

    def clear(self) -> None:
        """Remove all registered strategies.

        移除所有已注册的策略。
        """
        self._registry.clear()

    @property
    def size(self) -> int:
        """Number of registered strategies.

        已注册策略数量。
        """
        return len(self._registry)
