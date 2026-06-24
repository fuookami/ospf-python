"""令牌表注册辅助工具 / Token table registration support."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ospf_python.core.token.token_table import TokenTable

if TYPE_CHECKING:
    from ospf_python.core.token.token import Token


class TokenTableRegistrationSupport:
    """令牌表注册辅助工具 / Helper for registering tokens.

    提供令牌的批量注册、注销和查询功能。
    Provides batch registration, unregistration, and
    lookup for tokens.

    Attributes:
        _registered: 已注册令牌表 / Registered token table.
    """

    def __init__(self) -> None:
        """初始化注册辅助工具 / Initialize registration support."""
        self._registered = TokenTable()

    def register(self, token: Token, value: object) -> bool:
        """注册令牌 / Register token.

        Args:
            token: 待注册的令牌 / Token to register.
            value: 关联值 / Associated value.

        Returns:
            是否为新注册 / Whether this is a new registration.
        """
        is_new = not self._registered.contains(token)
        self._registered.set(token, value)
        return is_new

    def unregister(self, token: Token) -> bool:
        """注销令牌 / Unregister token.

        Args:
            token: 待注销的令牌 / Token to unregister.

        Returns:
            是否成功注销 / Whether unregistration succeeded.
        """
        return self._registered.remove(token)

    def is_registered(self, token: Token) -> bool:
        """判断令牌是否已注册 / Check if token is registered.

        Args:
            token: 目标令牌 / Target token.

        Returns:
            是否已注册 / Whether the token is registered.
        """
        return self._registered.contains(token)

    def get_value(self, token: Token) -> object | None:
        """获取已注册令牌的值 / Get value for registered token.

        Args:
            token: 目标令牌 / Target token.

        Returns:
            注册的值或 None / Registered value or None.
        """
        return self._registered.get(token)

    @property
    def registered_count(self) -> int:
        """获取已注册令牌数量 / Get registered token count.

        Returns:
            已注册数量 / Number of registered tokens.
        """
        return self._registered.size

    def clear(self) -> None:
        """清空所有注册 / Clear all registrations."""
        self._registered.clear()
