"""符号组合 / Symbol combination."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.token.token import Token


@dataclass(frozen=True)
class SymbolCombination:
    """符号组合 / Symbol combination.

    将多个符号组合为一个逻辑单元。
    Combines multiple symbols into a single logical unit.

    Attributes:
        name: 组合名称 / Combination name.
        tokens: 包含的令牌列表 / Contained token list.
    """

    name: str
    """组合名称 / Combination name."""

    tokens: tuple[Token, ...] = ()
    """包含的令牌列表 / Contained token list."""

    @property
    def size(self) -> int:
        """获取组合大小 / Get combination size.

        Returns:
            令牌数量 / Number of tokens.
        """
        return len(self.tokens)

    def contains(self, token: Token) -> bool:
        """判断是否包含令牌 / Check if token is contained.

        Args:
            token: 目标令牌 / Target token.

        Returns:
            是否包含 / Whether the token is contained.
        """
        return token in self.tokens

    def __len__(self) -> int:
        return len(self.tokens)

    def __iter__(self) -> Iterator[Token]:
        return iter(self.tokens)

    def __str__(self) -> str:
        return f"SymbolCombination({self.name}, size={self.size})"

    @staticmethod
    def create(
        *,
        name: str,
        tokens: tuple[Token, ...] = (),
    ) -> SymbolCombination:
        """创建符号组合 / Create symbol combination.

        Args:
            name: 组合名称 / Combination name.
            tokens: 令牌元组 / Token tuple.

        Returns:
            符号组合实例 / Symbol combination instance.
        """
        return SymbolCombination(name=name, tokens=tokens)
