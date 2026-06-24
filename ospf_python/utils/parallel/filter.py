"""并行过滤操作 / Parallel filter operation.

对应 Kotlin 端 filterParallel。
Mirrors the Kotlin filterParallel.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from typing import TypeVar

from ospf_python.utils.parallel.common import WorkerPoolResult

# T: 元素类型 / Element type
T = TypeVar("T")

# 默认并发限制 / Default concurrency limit
_DEFAULT_CONCURRENCY = 8


async def filter_parallel(
    items: Sequence[T],
    predicate: Callable[[T], bool],
    *,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> list[T]:
    """并行过滤列表元素 / Filter list elements in parallel.

    并发评估谓词，返回满足条件的元素，保持原始顺序。
    Concurrently evaluates the predicate and returns elements
    that satisfy it, preserving original order.

    Args:
        items: 待过滤的元素序列 / The sequence of elements to filter.
        predicate: 过滤谓词 / The filter predicate.
        concurrency: 最大并发数 / Maximum concurrency.

    Returns:
        满足谓词的元素列表（保持原始顺序） / List of elements
        satisfying the predicate (original order preserved).
    """
    if not items:
        return []

    semaphore = asyncio.Semaphore(concurrency)

    async def _evaluate(index: int, item: T) -> WorkerPoolResult[bool]:
        """带信号量的谓词评估 / Predicate evaluation with semaphore."""
        async with semaphore:
            result = predicate(item)
            if asyncio.iscoroutine(result):
                result = await result
            return WorkerPoolResult(index=index, result=bool(result))

    results = await asyncio.gather(
        *(_evaluate(i, item) for i, item in enumerate(items))
    )
    sorted_results = sorted(results, key=lambda r: r.index)
    return [item for item, r in zip(items, sorted_results, strict=False) if r.result]
