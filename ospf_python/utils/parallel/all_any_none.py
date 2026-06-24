"""并行全/任/无判断操作 / Parallel all/any/none operations.

对应 Kotlin 端 allParallel / anyParallel / noneParallel。
Mirrors the Kotlin allParallel, anyParallel, and
noneParallel.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from typing import TypeVar

# T: 元素类型 / Element type
T = TypeVar("T")

# 默认并发限制 / Default concurrency limit
_DEFAULT_CONCURRENCY = 8


async def all_parallel(
    items: Sequence[T],
    predicate: Callable[[T], bool],
    *,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> bool:
    """并行判断是否所有元素满足谓词 / Check if all elements
    satisfy the predicate in parallel.

    并发评估谓词，若任一不满足则立即返回 False。
    Concurrently evaluates the predicate; returns False
    immediately if any element fails.

    Args:
        items: 待检查的元素序列 / The sequence of elements to check.
        predicate: 检查谓词 / The check predicate.
        concurrency: 最大并发数 / Maximum concurrency.

    Returns:
        所有元素均满足谓词时为 True / True if all elements
        satisfy the predicate.
    """
    if not items:
        return True

    semaphore = asyncio.Semaphore(concurrency)
    fail_event = asyncio.Event()

    async def _check(item: T) -> bool:
        """带信号量的谓词检查 / Predicate check with semaphore."""
        async with semaphore:
            if fail_event.is_set():
                return True  # 已失败，跳过 / Already failed, skip
            result = predicate(item)
            if asyncio.iscoroutine(result):
                result = await result
            if not result:
                fail_event.set()
            return bool(result)

    results = await asyncio.gather(*(_check(item) for item in items))
    return all(results)


async def any_parallel(
    items: Sequence[T],
    predicate: Callable[[T], bool],
    *,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> bool:
    """并行判断是否有任一元素满足谓词 / Check if any element
    satisfies the predicate in parallel.

    并发评估谓词，若任一满足则立即返回 True。
    Concurrently evaluates the predicate; returns True
    immediately if any element succeeds.

    Args:
        items: 待检查的元素序列 / The sequence of elements to check.
        predicate: 检查谓词 / The check predicate.
        concurrency: 最大并发数 / Maximum concurrency.

    Returns:
        存在满足谓词的元素时为 True / True if any element
        satisfies the predicate.
    """
    if not items:
        return False

    semaphore = asyncio.Semaphore(concurrency)
    success_event = asyncio.Event()

    async def _check(item: T) -> bool:
        """带信号量的谓词检查 / Predicate check with semaphore."""
        async with semaphore:
            if success_event.is_set():
                return True  # 已成功，跳过 / Already succeeded, skip
            result = predicate(item)
            if asyncio.iscoroutine(result):
                result = await result
            if result:
                success_event.set()
            return bool(result)

    results = await asyncio.gather(*(_check(item) for item in items))
    return any(results)


async def none_parallel(
    items: Sequence[T],
    predicate: Callable[[T], bool],
    *,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> bool:
    """并行判断是否无元素满足谓词 / Check if no element satisfies
    the predicate in parallel.

    等价于 not any_parallel(items, predicate)。
    Equivalent to not any_parallel(items, predicate).

    Args:
        items: 待检查的元素序列 / The sequence of elements to check.
        predicate: 检查谓词 / The check predicate.
        concurrency: 最大并发数 / Maximum concurrency.

    Returns:
        无元素满足谓词时为 True / True if no element satisfies
        the predicate.
    """
    return not await any_parallel(items, predicate, concurrency=concurrency)
