"""Meta-programming 模块测试 / Tests for meta-programming utilities.

覆盖 lazy_delegate、name_transfer、naming_system。
Covers lazy_delegate, name_transfer, naming_system.
"""

from __future__ import annotations

from ospf_python.utils.meta_programming.lazy_delegate import (
    LazyDelegate,
    SelfLazyDelegate,
    SuspendLazy,
)
from ospf_python.utils.meta_programming.name_transfer import (
    NameTransfer,
    NameTransferCacheKey,
)
from ospf_python.utils.meta_programming.naming_system import NamingSystem

# -- NamingSystem --


class TestNamingSystem:
    """NamingSystem 枚举测试。"""

    def test_camel_case_value(self) -> None:
        """camelCase 值正确。"""
        assert NamingSystem.CAMEL_CASE.value == "camelCase"

    def test_snake_case_value(self) -> None:
        """snake_case 值正确。"""
        assert NamingSystem.SNAKE_CASE.value == "snake_case"

    def test_pascal_case_value(self) -> None:
        """PascalCase 值正确。"""
        assert NamingSystem.PASCAL_CASE.value == "PascalCase"

    def test_members_count(self) -> None:
        """枚举成员数量为 3。"""
        assert len(NamingSystem) == 3


# -- NameTransfer --


class TestNameTransfer:
    """NameTransfer 测试。"""

    def test_camel_to_snake(self) -> None:
        """camelCase 转 snake_case。"""
        nt = NameTransfer()
        assert nt.to_snake("userName") == "user_name"

    def test_snake_to_camel(self) -> None:
        """snake_case 转 camelCase。"""
        nt = NameTransfer()
        assert nt.to_camel("user_name") == "userName"

    def test_snake_to_pascal(self) -> None:
        """snake_case 转 PascalCase。"""
        nt = NameTransfer()
        assert nt.to_pascal("user_name") == "UserName"

    def test_pascal_to_snake(self) -> None:
        """PascalCase 转 snake_case。"""
        nt = NameTransfer()
        assert nt.to_snake("UserName") == "user_name"

    def test_camel_to_pascal(self) -> None:
        """camelCase 转 PascalCase。"""
        nt = NameTransfer()
        assert nt.to_pascal("userName") == "UserName"

    def test_pascal_to_camel(self) -> None:
        """PascalCase 转 camelCase。"""
        nt = NameTransfer()
        assert nt.to_camel("UserName") == "userName"

    def test_single_word(self) -> None:
        """单词名称。"""
        nt = NameTransfer()
        assert nt.to_snake("name") == "name"
        assert nt.to_camel("name") == "name"
        assert nt.to_pascal("name") == "Name"

    def test_caching(self) -> None:
        """缓存返回相同结果。"""
        nt = NameTransfer()
        r1 = nt.to_snake("firstName")
        r2 = nt.to_snake("firstName")
        assert r1 == r2
        key = NameTransferCacheKey(name="firstName", system=NamingSystem.SNAKE_CASE)
        assert key in nt._cache

    def test_multi_word_snake(self) -> None:
        """多段 snake_case。"""
        nt = NameTransfer()
        assert nt.to_snake("first_name_last") == "first_name_last"

    def test_uppercase_acronym(self) -> None:
        """大写缩写词处理。"""
        nt = NameTransfer()
        result = nt.to_snake("HTTPServer")
        assert "http" in result.lower() or "h_t_t_p" in result.lower()


# -- LazyDelegate --


class TestLazyDelegate:
    """LazyDelegate 描述符测试。"""

    def test_lazy_value_computed_once(self) -> None:
        """惰性值仅计算一次。"""
        call_count = 0

        class Foo:
            value = LazyDelegate(lambda: _compute())

        def _compute() -> int:
            nonlocal call_count
            call_count += 1
            return 42

        foo = Foo()
        assert foo.value == 42
        assert foo.value == 42
        assert call_count == 1

    def test_lazy_class_access(self) -> None:
        """类访问返回描述符自身。"""

        class Foo:
            value = LazyDelegate(lambda: 1)

        assert isinstance(Foo.value, LazyDelegate)

    def test_lazy_per_instance(self) -> None:
        """每个实例独立缓存。"""

        class Foo:
            value = LazyDelegate(lambda: 99)

        a = Foo()
        b = Foo()
        assert a.value == 99
        assert b.value == 99


# -- SelfLazyDelegate --


class TestSelfLazyDelegate:
    """SelfLazyDelegate 描述符测试。"""

    def test_self_lazy_receives_instance(self) -> None:
        """工厂函数接收实例自身。"""

        class Foo:
            def __init__(self, base: int) -> None:
                self.base = base

            doubled = SelfLazyDelegate(lambda self: self.base * 2)

        foo = Foo(5)
        assert foo.doubled == 10

    def test_self_lazy_cached(self) -> None:
        """结果被缓存。"""
        call_count = 0

        class Foo:
            def __init__(self, val: int) -> None:
                self.val = val

            computed = SelfLazyDelegate(lambda self: _calc(self))

        def _calc(inst: Foo) -> int:
            nonlocal call_count
            call_count += 1
            return inst.val + 1

        foo = Foo(10)
        assert foo.computed == 11
        assert foo.computed == 11
        assert call_count == 1

    def test_self_lazy_class_access(self) -> None:
        """类访问返回描述符自身。"""

        class Foo:
            value = SelfLazyDelegate(lambda self: 1)

        assert isinstance(Foo.value, SelfLazyDelegate)


# -- SuspendLazy --


class TestSuspendLazy:
    """SuspendLazy 异步惰性求值测试。"""

    async def test_basic(self) -> None:
        """基本异步惰性求值。"""
        sl = SuspendLazy(lambda: 42)
        result = await sl.get()
        assert result == 42

    async def test_cached(self) -> None:
        """结果被缓存。"""
        call_count = 0

        async def factory() -> int:
            nonlocal call_count
            call_count += 1
            return 99

        sl = SuspendLazy(factory)
        assert await sl.get() == 99
        assert await sl.get() == 99
        assert call_count == 1

    async def test_async_factory(self) -> None:
        """支持异步工厂函数。"""

        async def factory() -> str:
            return "hello"

        sl = SuspendLazy(factory)
        assert await sl.get() == "hello"

    async def test_concurrent_access(self) -> None:
        """并发访问安全。"""
        call_count = 0

        async def factory() -> int:
            nonlocal call_count
            call_count += 1
            return 1

        sl = SuspendLazy(factory)
        import asyncio

        results = await asyncio.gather(sl.get(), sl.get(), sl.get())
        assert all(r == 1 for r in results)
        assert call_count == 1
