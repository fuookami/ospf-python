"""令牌缓存键 / Token cache key."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.token.token import Token


@dataclass(frozen=True)
class TokenCacheKey:
    """令牌缓存键 / Token cache key.

    由令牌和操作标识组成，用于缓存查找。
    Composed of a token and operation identifier for cache
    lookup.

    Attributes:
        token: 目标令牌 / Target token.
        operation: 操作标识 / Operation identifier.
    """

    token: Token
    """目标令牌 / Target token."""

    operation: str
    """操作标识 / Operation identifier."""

    def __str__(self) -> str:
        return f"{self.token}:{self.operation}"

    def __hash__(self) -> int:
        return hash((self.token, self.operation))

    @staticmethod
    def create(
        *,
        token: Token,
        operation: str,
    ) -> TokenCacheKey:
        """创建缓存键 / Create cache key.

        Args:
            token: 目标令牌 / Target token.
            operation: 操作标识 / Operation identifier.

        Returns:
            缓存键实例 / Cache key instance.
        """
        return TokenCacheKey(token=token, operation=operation)
