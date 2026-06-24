"""并行查找操作 / Parallel find operation.

对应 Kotlin 端 findParallel。
Mirrors the Kotlin findParallel.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from typing import TypeVar

# T: 元素类型 / Element type
T = TypeVar("T")

# 默认并发限制 / Default concurrency limit
_DEFAULT_CONCURRENCY = 8


async def find_parallel(
    items: Sequence[T],
    predicate: Callable[[T], bool],
    *,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> T | None:
    """并行查找第一个匹配元素 / Find the first matching element
    in parallel.

    并发评估谓词，返回第一个满足条件的元素。
    Concurrently evaluates the predicate and returns the first
    element that satisfies it.

    Args:
        items: 待搜索的元素序列 / The sequence of elements to search.
        predicate: 匹配谓词 / The match predicate.
        concurrency: 最大并发数 / Maximum concurrency.

    Returns:
        第一个满足谓词的元素，未找到则返回 None。
        The first element satisfying the predicate, or None if
        not found.
    """
    if not items:
        return None

    semaphore = asyncio.Semaphore(concurrency)
    found_event = asyncio.Event()
    result: T | None = None

    async def _check(item: T) -> bool:
        """带信号量的谓词检查 / Predicate check with semaphore."""
        nonlocal result
        async with semaphore:
            if found_event.is_set():
                return False
            match = predicate(item)
            if asyncio.iscoroutine(match):
                match = await match
            if match and not found_event.is_set():
                result = item
                found_event.set()
                return True
            return False

    await asyncio.gather(*(_check(item) for item in items))
    return result
