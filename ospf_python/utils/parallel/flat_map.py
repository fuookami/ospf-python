"""并行扁平映射操作 / Parallel flat map operation.

对应 Kotlin 端 flatMapParallel。
Mirrors the Kotlin flatMapParallel.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from typing import TypeVar

from ospf_python.utils.parallel.common import WorkerPoolResult

# T: 输入类型 / Input type
T = TypeVar("T")

# U: 输出元素类型 / Output element type
U = TypeVar("U")

# 默认并发限制 / Default concurrency limit
_DEFAULT_CONCURRENCY = 8


async def flat_map_parallel(
    items: Sequence[T],
    transform: Callable[[T], Sequence[U]],
    *,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> list[U]:
    """并行扁平映射 / Flat map in parallel.

    并发执行转换函数，将所有结果展平为单一列表，保持顺序。
    Concurrently executes the transform function and flattens
    all results into a single list, preserving order.

    Args:
        items: 待转换的元素序列 / The sequence of elements to
            transform.
        transform: 返回序列的转换函数 / Transform function
            returning a sequence.
        concurrency: 最大并发数 / Maximum concurrency.

    Returns:
        展平后的结果列表 / The flattened result list.
    """
    if not items:
        return []

    semaphore = asyncio.Semaphore(concurrency)

    async def _run(index: int, item: T) -> WorkerPoolResult[Sequence[U]]:
        """带信号量的任务执行 / Task execution with semaphore."""
        async with semaphore:
            result = transform(item)
            if asyncio.iscoroutine(result):
                result = await result
            return WorkerPoolResult(index=index, result=result)

    results = await asyncio.gather(*(_run(i, item) for i, item in enumerate(items)))
    sorted_results = sorted(results, key=lambda r: r.index)
    # 展平结果 / Flatten results
    flat: list[U] = []
    for r in sorted_results:
        flat.extend(r.result)
    return flat
