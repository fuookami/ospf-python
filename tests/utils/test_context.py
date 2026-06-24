"""Context 上下文机制测试。

测试 Context、ContextKey、ContextVar 的行为。
"""

from __future__ import annotations

from ospf_python.utils.context import Context, ContextKey, ContextVar


class TestContextKey:
    """ContextKey 上下文键测试。"""

    def test_create_key_with_name(self) -> None:
        key = ContextKey(name="user_id")
        assert key.name == "user_id"

    def test_key_equality(self) -> None:
        k1 = ContextKey(name="x")
        k2 = ContextKey(name="x")
        assert k1 == k2

    def test_key_inequality(self) -> None:
        k1 = ContextKey(name="a")
        k2 = ContextKey(name="b")
        assert k1 != k2


class TestContextVar:
    """ContextVar 上下文变量测试。"""

    def test_var_with_key_and_value(self) -> None:
        key = ContextKey(name="count")
        var = ContextVar(key=key, value=0)
        assert var.key == key
        assert var.value == 0

    def test_var_set_and_get(self) -> None:
        key = ContextKey(name="name")
        var = ContextVar(key=key, value="Alice")
        assert var.value == "Alice"

    def test_var_different_values(self) -> None:
        key = ContextKey(name="name")
        var1 = ContextVar(key=key, value="Bob")
        var2 = ContextVar(key=key, value="Charlie")
        assert var1.value == "Bob"
        assert var2.value == "Charlie"


class TestContext:
    """Context 上下文容器测试。"""

    def test_context_empty(self) -> None:
        ctx: Context[str] = Context()
        key = ContextKey(name="missing")
        assert ctx.get(key) is None

    def test_context_set_and_get(self) -> None:
        ctx: Context[str] = Context()
        key = ContextKey(name="host")
        ctx.set(key, "localhost")
        assert ctx.get(key) == "localhost"

    def test_context_get_missing_returns_none(self) -> None:
        ctx: Context[int] = Context()
        key = ContextKey(name="missing")
        assert ctx.get(key) is None

    def test_context_get_missing_with_default(self) -> None:
        ctx: Context[int] = Context()
        key = ContextKey(name="missing", default_factory=lambda: 42)
        assert ctx.get_or_default(key) == 42

    def test_context_overwrite(self) -> None:
        ctx: Context[str] = Context()
        key = ContextKey(name="host")
        ctx.set(key, "a")
        ctx.set(key, "b")
        assert ctx.get(key) == "b"

    def test_context_multiple_keys(self) -> None:
        ctx: Context = Context()
        k1 = ContextKey(name="a")
        k2 = ContextKey(name="b")
        ctx.set(k1, "hello")
        ctx.set(k2, 42)
        assert ctx.get(k1) == "hello"
        assert ctx.get(k2) == 42

    def test_context_contains(self) -> None:
        ctx: Context[str] = Context()
        key = ContextKey(name="x")
        assert ctx.contains(key) is False
        ctx.set(key, "v")
        assert ctx.contains(key) is True
