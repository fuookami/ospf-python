"""条件与查找结果 / Condition and find result.

Condition[T] 和 ListFindResult[T]，对应 Kotlin 数据类。
Condition[T] and ListFindResult[T], corresponding to Kotlin data classes.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Condition(Generic[T]):
    """条件包装器 / Condition wrapper.

    对应 Kotlin `data class Condition<T>(val pred: (T) -> Boolean)`。
    Corresponds to Kotlin `data class Condition<T>(val pred: (T) -> Boolean)`.

    Args:
        predicate: 谓词函数 / Predicate function.
    """

    _predicate: Callable[[T], bool]

    @property
    def predicate(self) -> Callable[[T], bool]:
        """获取谓词 / Get predicate."""
        return self._predicate

    def __call__(self, value: T) -> bool:
        """调用条件 / Invoke condition."""
        return self._predicate(value)


@dataclass(frozen=True)
class ListFindResult(Generic[T]):
    """列表查找结果 / List find result.

    对应 Kotlin `data class ListFindResult<T>(val index: Int, val value: T)`。
    Corresponds to Kotlin `data class ListFindResult<T>(val index: Int, val value: T)`.

    Args:
        index: 查找位置 / Found index.
        value: 查找值 / Found value.
    """

    _index: int
    _value: T

    @property
    def index(self) -> int:
        """获取索引 / Get index."""
        return self._index

    @property
    def value(self) -> T:
        """获取值 / Get value."""
        return self._value
