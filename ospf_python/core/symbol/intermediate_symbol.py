"""中间符号定义 / Intermediate symbol definition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.token.token import Token


@dataclass(frozen=True)
class IntermediateSymbol:
    """中间符号 / Intermediate symbol.

    表示优化模型中的中间表达式符号，由令牌和
    表达式名称组成。
    Represents an intermediate expression symbol in an
    optimization model, composed of a token and expression name.

    Attributes:
        token: 关联令牌 / Associated token.
        expression_name: 表达式名称 / Expression name.
    """

    token: Token
    """关联令牌 / Associated token."""

    expression_name: str
    """表达式名称 / Expression name."""

    @property
    def name(self) -> str:
        """获取符号名称 / Get symbol name.

        Returns:
            令牌名称 / Token name.
        """
        return self.token.name

    @property
    def index(self) -> int:
        """获取符号索引 / Get symbol index.

        Returns:
            令牌索引 / Token index.
        """
        return self.token.index

    def __str__(self) -> str:
        return f"{self.expression_name}({self.token})"

    @staticmethod
    def create(
        *,
        token: Token,
        expression_name: str,
    ) -> IntermediateSymbol:
        """创建中间符号 / Create intermediate symbol.

        Args:
            token: 关联令牌 / Associated token.
            expression_name: 表达式名称 / Expression name.

        Returns:
            中间符号实例 / Intermediate symbol instance.
        """
        return IntermediateSymbol(
            token=token,
            expression_name=expression_name,
        )
