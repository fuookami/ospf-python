"""令牌定义 / Token definition."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    """令牌 / Token.

    优化模型中的基本标识单元。
    A basic identification unit in an optimization model.

    Attributes:
        name: 令牌名称 / Token name.
        index: 令牌索引 / Token index.
    """

    name: str
    """令牌名称 / Token name."""

    index: int
    """令牌索引 / Token index."""

    def __str__(self) -> str:
        return f"{self.name}[{self.index}]"

    def __hash__(self) -> int:
        return hash((self.name, self.index))

    @staticmethod
    def create(
        *,
        name: str,
        index: int,
    ) -> Token:
        """创建令牌 / Create token.

        Args:
            name: 令牌名称 / Token name.
            index: 令牌索引 / Token index.

        Returns:
            令牌实例 / Token instance.
        """
        return Token(name=name, index=index)
