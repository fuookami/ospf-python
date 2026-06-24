"""中间符号表达式支持 / Intermediate symbol expression support."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.symbol.intermediate_symbol import (
        IntermediateSymbol,
    )


@dataclass(frozen=True)
class IntermediateSymbolExpressionSupport:
    """中间符号表达式辅助工具 / Intermediate symbol expression helper.

    管理中间符号与其表达式的映射关系。
    Manages mappings between intermediate symbols and
    their expressions.

    Attributes:
        _registry: 符号到表达式的注册表 / Symbol-to-expression registry.
    """

    _registry: dict[str, str] = field(default_factory=dict)
    """符号到表达式的注册表 / Symbol-to-expression registry."""

    def register(
        self,
        symbol: IntermediateSymbol,
        expression: str,
    ) -> None:
        """注册符号表达式 / Register symbol expression.

        Args:
            symbol: 中间符号 / Intermediate symbol.
            expression: 表达式字符串 / Expression string.
        """
        self._registry[symbol.expression_name] = expression

    def resolve(
        self,
        symbol: IntermediateSymbol,
    ) -> str | None:
        """解析符号表达式 / Resolve symbol expression.

        Args:
            symbol: 中间符号 / Intermediate symbol.

        Returns:
            表达式字符串或 None / Expression string or None.
        """
        return self._registry.get(symbol.expression_name)

    def is_registered(
        self,
        symbol: IntermediateSymbol,
    ) -> bool:
        """判断符号是否已注册 / Check if symbol is registered.

        Args:
            symbol: 中间符号 / Intermediate symbol.

        Returns:
            是否已注册 / Whether the symbol is registered.
        """
        return symbol.expression_name in self._registry

    @property
    def count(self) -> int:
        """获取已注册数量 / Get registered count.

        Returns:
            已注册表达式数量 / Number of registered expressions.
        """
        return len(self._registry)

    def clear(self) -> None:
        """清空注册表 / Clear registry."""
        self._registry.clear()
