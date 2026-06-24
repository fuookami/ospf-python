"""并行计数操作 / Parallel count operation.

对应 Kotlin 端 countParallel。
Mirrors the Kotlin countParallel.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from typing import TypeVar

# T: 元素类型 / Element type
T = TypeVar("T")

# 默认并发限制 / Default concurrency limit
_DEFAULT_CONCURRENCY = 8


async def count_parallel(
    items: Sequence[T],
    predicate: Callable[[T], bool],
    *,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> int:
    """并行计数满足谓词的元素 / Count elements satisfying the
    predicate in parallel.

    并发评估谓词，统计满足条件的元素数量。
    Concurrently evaluates the predicate and counts the number
    of elements satisfying it.

    Args:
        items: 待计数的元素序列 / The sequence of elements to count.
        predicate: 匹配谓词 / The match predicate.
        concurrency: 最大并发数 / Maximum concurrency.

    Returns:
        满足谓词的元素数量 / The count of elements satisfying the
        predicate.
    """
    if not items:
        return 0

    semaphore = asyncio.Semaphore(concurrency)

    async def _check(item: T) -> int:
        """带信号量的谓词检查 / Predicate check with semaphore."""
        async with semaphore:
            result = predicate(item)
            if asyncio.iscoroutine(result):
                result = await result
            return 1 if result else 0

    results = await asyncio.gather(*(_check(item) for item in items))
    return sum(results)
