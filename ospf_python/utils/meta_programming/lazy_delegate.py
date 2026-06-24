"""惰性委托描述符 / Lazy delegate descriptors.

对应 Kotlin 端 LazyDelegate / SelfLazyDelegate / SuspendLazy。
Mirrors the Kotlin LazyDelegate, SelfLazyDelegate, and SuspendLazy.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Generic, TypeVar

# T: 实例类型 / Instance type
T = TypeVar("T")

# U: 值类型 / Value type
U = TypeVar("U")


class LazyDelegate(Generic[T, U]):
    """惰性委托描述符 / Lazy delegate descriptor.

    对应 Kotlin 的 LazyDelegate<T, U>。
    首次访问时通过工厂函数计算值，之后缓存结果。
    Mirrors Kotlin's LazyDelegate<T, U>. Computes the value via a
    factory on first access, then caches the result.

    Attributes:
        _factory: 值工厂函数 / The value factory callable.
        _attr_name: 缓存属性名称 / The cache attribute name.
    """

    def __init__(self, factory: Callable[[], U]) -> None:
        """初始化惰性委托 / Initialize the lazy delegate.

        Args:
            factory: 计算值的工厂函数 / Factory function to compute
                the value.
        """
        self._factory: Callable[[], U] = factory
        self._attr_name: str = f"_lazy_{id(factory)}"

    def __set_name__(self, owner: type, name: str) -> None:
        """设置描述符名称 / Set the descriptor name.

        Args:
            owner: 拥有此描述符的类 / The class owning this descriptor.
            name: 属性名称 / The attribute name.
        """
        self._attr_name = f"_lazy_{name}"

    def __get__(self, instance: T | None, owner: type) -> U:
        """获取惰性值 / Get the lazy value.

        首次调用时计算并缓存，后续调用直接返回缓存值。
        Computes and caches on first call; returns the cached
        value on subsequent calls.

        Args:
            instance: 类实例，类访问时为 None / The class instance,
                or None when accessed from the class.
            owner: 拥有此描述符的类 / The class owning this descriptor.

        Returns:
            惰性计算的值 / The lazily computed value.
        """
        if instance is None:
            return self  # type: ignore[return-value]

        cached = getattr(instance, self._attr_name, _SENTINEL)
        if cached is _SENTINEL:
            value = self._factory()
            object.__setattr__(instance, self._attr_name, value)
            return value
        return cached  # type: ignore[return-value]


class SelfLazyDelegate(Generic[T, U]):
    """带自引用的惰性委托描述符 / Lazy delegate with self reference.

    对应 Kotlin 的 SelfLazyDelegate<T, U>。
    工厂函数接收实例自身作为参数，允许基于实例状态计算值。
    Mirrors Kotlin's SelfLazyDelegate<T, U>. The factory receives
    the instance itself, allowing value computation based on
    instance state.

    Attributes:
        _factory: 接收实例的工厂函数 / Factory function receiving
            the instance.
        _attr_name: 缓存属性名称 / The cache attribute name.
    """

    def __init__(self, factory: Callable[[T], U]) -> None:
        """初始化带自引用的惰性委托 / Initialize the self-referencing
        lazy delegate.

        Args:
            factory: 接收实例的工厂函数 / Factory function that
                receives the instance.
        """
        self._factory: Callable[[T], U] = factory
        self._attr_name: str = f"_self_lazy_{id(factory)}"

    def __set_name__(self, owner: type, name: str) -> None:
        """设置描述符名称 / Set the descriptor name.

        Args:
            owner: 拥有此描述符的类 / The class owning this descriptor.
            name: 属性名称 / The attribute name.
        """
        self._attr_name = f"_self_lazy_{name}"

    def __get__(self, instance: T | None, owner: type) -> U:
        """获取惰性值 / Get the lazy value.

        首次调用时将实例传给工厂函数计算并缓存。
        Passes the instance to the factory on first call, then
        caches the result.

        Args:
            instance: 类实例 / The class instance.
            owner: 拥有此描述符的类 / The class owning this descriptor.

        Returns:
            惰性计算的值 / The lazily computed value.
        """
        if instance is None:
            return self  # type: ignore[return-value]

        cached = getattr(instance, self._attr_name, _SENTINEL)
        if cached is _SENTINEL:
            value = self._factory(instance)
            object.__setattr__(instance, self._attr_name, value)
            return value
        return cached  # type: ignore[return-value]


class SuspendLazy(Generic[T]):
    """异步惰性求值 / Async lazy evaluation.

    对应 Kotlin 的 SuspendLazy<T>。
    通过异步工厂函数惰性计算值，使用锁保证线程安全。
    Mirrors Kotlin's SuspendLazy<T>. Lazily computes a value via
    an async factory, using a lock for thread safety.

    Attributes:
        _factory: 异步工厂函数 / The async factory callable.
        _value: 缓存的值 / The cached value.
        _initialized: 是否已初始化 / Whether initialized.
        _lock: 异步锁 / The async lock.
    """

    def __init__(self, factory: Callable[[], U]) -> None:
        """初始化异步惰性求值 / Initialize the async lazy.

        Args:
            factory: 异步工厂函数 / Async factory callable.
        """
        self._factory: Callable[[], U] = factory
        self._value: U | None = None
        self._initialized: bool = False
        self._lock: asyncio.Lock = asyncio.Lock()

    async def get(self) -> U:
        """获取异步惰性值 / Get the async lazy value.

        首次调用时异步计算并缓存，后续调用直接返回。
        Computes asynchronously on first call and caches; returns
        the cached value on subsequent calls.

        Returns:
            异步惰性计算的值 / The asynchronously lazily computed value.
        """
        if self._initialized:
            return self._value  # type: ignore[return-value]

        async with self._lock:
            # 双重检查 / Double-check
            if self._initialized:
                return self._value
            self._value = self._factory()
            # 如果工厂返回协程则 await / Await if factory returns coroutine
            if asyncio.iscoroutine(self._value):
                self._value = await self._value
            self._initialized = True
            return self._value  # type: ignore[return-value]


# 内部哨兵值 / Internal sentinel value
class _Sentinel:
    """标识未缓存的哨兵 / Sentinel for uncached values."""

    pass


_SENTINEL = _Sentinel()
