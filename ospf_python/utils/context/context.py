"""上下文系统 / Context system."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ContextKey:
    """上下文键 / Context key.

    Args:
        name: 键名 / Key name.
        default_factory: 默认值工厂 / Default value factory.
    """

    name: str
    default_factory: Callable[[], object] | None = None


@dataclass(frozen=True)
class ContextVar(Generic[T]):
    """上下文变量 / Context variable.

    Args:
        key: 上下文键 / Context key.
        value: 变量值 / Variable value.
    """

    key: ContextKey
    value: T


class Context(Generic[T]):
    """上下文容器 / Context container.

    Dict-like container for contextual values.
    """

    def __init__(self) -> None:
        self._data: dict[ContextKey, object] = {}

    def get(self, key: ContextKey) -> T | None:
        """获取值 / Get value."""
        return self._data.get(key)  # type: ignore[return-value]

    def set(self, key: ContextKey, value: T) -> None:
        """设置值 / Set value."""
        self._data[key] = value

    def contains(self, key: ContextKey) -> bool:
        """检查是否包含键 / Check if key is present."""
        return key in self._data

    def get_or_default(self, key: ContextKey) -> T:
        """获取值或默认值 / Get value or default."""
        if key in self._data:
            return self._data[key]  # type: ignore[return-value]
        if key.default_factory is not None:
            return key.default_factory()  # type: ignore[return-value]
        raise KeyError(f"Key '{key.name}' not found and no default factory")
