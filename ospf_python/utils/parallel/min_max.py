"""并行最小最大值操作 / Parallel min-max operation.

对应 Kotlin 端 minMaxParallel。
Mirrors the Kotlin minMaxParallel.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

# T: 元素类型 / Element type
T = TypeVar("T")


@dataclass(frozen=True)
class MinMaxResult(Generic[T]):
    """最小最大值结果 / Min-max result.

    包含同时找到的最小值和最大值。
    Contains both the minimum and maximum values found.

    Attributes:
        min_value: 最小值 / The minimum value.
        max_value: 最大值 / The maximum value.
    """

    min_value: T
    max_value: T


async def min_max_parallel(
    items: Sequence[T],
    comparator: Callable[[T, T], int] | None = None,
) -> MinMaxResult[T] | None:
    """并行查找最小值和最大值 / Find both min and max values
    in parallel.

    使用两次并发遍历分别查找最小值和最大值。
    Uses two concurrent passes to find the min and max values
    separately.

    Args:
        items: 待搜索的元素序列 / The sequence of elements to search.
        comparator: 可选比较函数 / Optional comparator function.

    Returns:
        包含最小值和最大值的结果，列表为空时返回 None。
        Result containing both min and max, or None if the list
        is empty.
    """
    if not items:
        return None

    if comparator is None:
        # 默认使用 < 运算符 / Default to < operator
        def _default_cmp(a: T, b: T) -> int:
            if a < b:  # type: ignore[operator]
                return -1
            if a > b:  # type: ignore[operator]
                return 1
            return 0

        comparator = _default_cmp

    async def _find_min() -> T:
        """查找最小值 / Find the minimum value."""
        best = items[0]
        for item in items[1:]:
            result = comparator(item, best)
            if asyncio.iscoroutine(result):
                result = await result
            if result < 0:
                best = item
        return best

    async def _find_max() -> T:
        """查找最大值 / Find the maximum value."""
        best = items[0]
        for item in items[1:]:
            result = comparator(item, best)
            if asyncio.iscoroutine(result):
                result = await result
            if result > 0:
                best = item
        return best

    min_val, max_val = await asyncio.gather(_find_min(), _find_max())
    return MinMaxResult(min_value=min_val, max_value=max_val)
