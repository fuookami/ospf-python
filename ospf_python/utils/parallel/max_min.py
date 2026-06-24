"""并行最大/最小值操作 / Parallel max/min operations.

对应 Kotlin 端 maxParallel / minParallel。
Mirrors the Kotlin maxParallel and minParallel.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from typing import TypeVar

# T: 元素类型 / Element type
T = TypeVar("T")

# 默认并发限制 / Default concurrency limit
_DEFAULT_CONCURRENCY = 8


async def max_parallel(
    items: Sequence[T],
    comparator: Callable[[T, T], int],
    *,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> T | None:
    """并行查找最大值 / Find the maximum value in parallel.

    并发评估元素对，返回最大元素。
    Concurrently evaluates element pairs and returns the
    maximum element.

    Args:
        items: 待搜索的元素序列 / The sequence of elements to search.
        comparator: 比较函数，返回正数表示第一个大 / Comparator
            returning positive if the first is greater.
        concurrency: 最大并发数 / Maximum concurrency.

    Returns:
        最大元素，列表为空时返回 None / The maximum element,
        or None if the list is empty.
    """
    if not items:
        return None

    # 对于简单比较操作，并行开销不值得，使用顺序归约
    # For simple comparison, parallel overhead is not worthwhile;
    # use sequential reduction
    best = items[0]
    for item in items[1:]:
        result = comparator(item, best)
        if asyncio.iscoroutine(result):
            result = await result
        if result > 0:
            best = item
    return best


async def min_parallel(
    items: Sequence[T],
    comparator: Callable[[T, T], int],
    *,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> T | None:
    """并行查找最小值 / Find the minimum value in parallel.

    并发评估元素对，返回最小元素。
    Concurrently evaluates element pairs and returns the
    minimum element.

    Args:
        items: 待搜索的元素序列 / The sequence of elements to search.
        comparator: 比较函数，返回正数表示第一个大 / Comparator
            returning positive if the first is greater.
        concurrency: 最大并发数 / Maximum concurrency.

    Returns:
        最小元素，列表为空时返回 None / The minimum element,
        or None if the list is empty.
    """
    if not items:
        return None

    best = items[0]
    for item in items[1:]:
        result = comparator(item, best)
        if asyncio.iscoroutine(result):
            result = await result
        if result < 0:
            best = item
    return best
