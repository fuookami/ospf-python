"""TokenTableRegistrationSupport 测试。

测试令牌表注册辅助工具的注册、注销和查询。
Tests registration support register, unregister, and query.
"""

from __future__ import annotations

from ospf_python.core.token.token import Token
from ospf_python.core.token.token_table_registration_support import (
    TokenTableRegistrationSupport,
)


class TestTokenTableRegistrationSupportRegister:
    """注册测试 / Registration tests."""

    def test_register_new_token(self) -> None:
        """注册新令牌。/ Register new token."""
        reg = TokenTableRegistrationSupport()
        t = Token(name="x", index=0)
        assert reg.register(t, "value") is True
        assert reg.is_registered(t) is True

    def test_register_existing_token(self) -> None:
        """注册已存在令牌。/ Register existing token."""
        reg = TokenTableRegistrationSupport()
        t = Token(name="x", index=0)
        reg.register(t, "v1")
        assert reg.register(t, "v2") is False


class TestTokenTableRegistrationSupportUnregister:
    """注销测试 / Unregister tests."""

    def test_unregister(self) -> None:
        """注销令牌。/ Unregister token."""
        reg = TokenTableRegistrationSupport()
        t = Token(name="x", index=0)
        reg.register(t, "v")
        assert reg.unregister(t) is True
        assert reg.is_registered(t) is False

    def test_unregister_missing_returns_false(self) -> None:
        """注销不存在返回 False。/ Unregister missing."""
        reg = TokenTableRegistrationSupport()
        t = Token(name="x", index=0)
        assert reg.unregister(t) is False


class TestTokenTableRegistrationSupportQuery:
    """查询测试 / Query tests."""

    def test_get_value(self) -> None:
        """获取注册值。/ Get registered value."""
        reg = TokenTableRegistrationSupport()
        t = Token(name="x", index=0)
        reg.register(t, 42)
        assert reg.get_value(t) == 42

    def test_get_value_missing_returns_none(self) -> None:
        """获取不存在返回 None。/ Get missing returns None."""
        reg = TokenTableRegistrationSupport()
        t = Token(name="x", index=0)
        assert reg.get_value(t) is None

    def test_registered_count(self) -> None:
        """已注册数量。/ Registered count."""
        reg = TokenTableRegistrationSupport()
        assert reg.registered_count == 0
        reg.register(Token(name="a", index=0), 1)
        reg.register(Token(name="b", index=1), 2)
        assert reg.registered_count == 2

    def test_clear(self) -> None:
        """清空注册。/ Clear registrations."""
        reg = TokenTableRegistrationSupport()
        reg.register(Token(name="a", index=0), 1)
        reg.register(Token(name="b", index=1), 2)
        reg.clear()
        assert reg.registered_count == 0
