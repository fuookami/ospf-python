"""Generation strategy enumeration.

生成策略枚举 / Generation strategy enumeration.
"""

from __future__ import annotations

from enum import StrEnum


class GenerationStrategy(StrEnum):
    """Strategy for generating scheduling bunches.

    生成调度任务组的策略。
    """

    GREEDY = "GREEDY"
    BALANCED = "BALANCED"
    PRIORITY = "PRIORITY"

    @property
    def description(self) -> str:
        """Bilingual description of the strategy.

        策略的中英文描述。
        """
        descriptions: dict[GenerationStrategy, str] = {
            GenerationStrategy.GREEDY: (
                "贪心策略：优先填满容量 / Greedy: fill capacity first"
            ),
            GenerationStrategy.BALANCED: (
                "均衡策略：均匀分配负载 / Balanced: distribute load evenly"
            ),
            GenerationStrategy.PRIORITY: (
                "优先级策略：按优先级分组 / Priority: group by priority level"
            ),
        }
        return descriptions[self]

    @property
    def short_name(self) -> str:
        """Short identifier for the strategy.

        策略的短标识符。
        """
        names: dict[GenerationStrategy, str] = {
            GenerationStrategy.GREEDY: "greedy",
            GenerationStrategy.BALANCED: "balanced",
            GenerationStrategy.PRIORITY: "priority",
        }
        return names[self]
