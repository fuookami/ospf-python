"""展平工具 / Flatten utility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.token.token import Token


@dataclass(frozen=True)
class FlattenUtility:
    """表达式展平工具 / Expression flatten utility.

    将嵌套表达式结构展平为令牌列表。
    Flattens nested expression structures into a token list.

    Attributes:
        _max_depth: 最大递归深度 / Maximum recursion depth.
    """

    _max_depth: int = 100
    """最大递归深度 / Maximum recursion depth."""

    def flatten(
        self,
        expr: object,
    ) -> list[Token]:
        """展平表达式 / Flatten expression.

        将嵌套的表达式树展平为线性令牌列表。
        Flattens a nested expression tree into a linear
        token list.

        Args:
            expr: 待展平的表达式 / Expression to flatten.

        Returns:
            展平后的令牌列表 / Flattened token list.
        """
        result: list[Token] = []
        self._flatten_recursive(expr, result, 0)
        return result

    def _flatten_recursive(
        self,
        node: object,
        result: list[Token],
        depth: int,
    ) -> None:
        """递归展平 / Recursive flatten.

        Args:
            node: 当前节点 / Current node.
            result: 结果列表 / Result list.
            depth: 当前深度 / Current depth.
        """
        if depth >= self._max_depth:
            return

        if hasattr(node, "tokens"):
            for child in node.tokens:
                self._flatten_recursive(child, result, depth + 1)
        elif hasattr(node, "token"):
            result.append(node.token)
        elif hasattr(node, "name") and hasattr(node, "index"):
            result.append(node)  # type: ignore[arg-type]

    @staticmethod
    def create(
        *,
        max_depth: int = 100,
    ) -> FlattenUtility:
        """创建展平工具 / Create flatten utility.

        Args:
            max_depth: 最大递归深度 / Maximum recursion depth.

        Returns:
            展平工具实例 / Flatten utility instance.
        """
        return FlattenUtility(_max_depth=max_depth)
