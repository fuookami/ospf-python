"""松弛函数符号 / Slack function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class Slack(FunctionSymbol):
    """松弛 / Slack.

    松弛函数符号实现。
    Slack function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
    """

    name: str = "Slack"
    """函数符号名称 / Function symbol name."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        if not args:
            return 0.0
        return max(0.0, args[0])

    @staticmethod
    def create() -> Slack:
        """创建松弛 / Create Slack.

        Returns:
            松弛实例 / Slack instance.
        """
        return Slack(name="Slack")
