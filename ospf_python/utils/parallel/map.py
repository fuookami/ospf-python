"""并行映射操作 / Parallel map operation.

对应 Kotlin 端 mapParallel。
Mirrors the Kotlin mapParallel.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from typing import TypeVar

from ospf_python.utils.parallel.common import WorkerPoolResult

# T: 输入类型 / Input type
T = TypeVar("T")

# U: 输出类型 / Output type
U = TypeVar("U")

# 默认并发限制 / Default concurrency limit
_DEFAULT_CONCURRENCY = 8


async def map_parallel(
    items: Sequence[T],
    transform: Callable[[T], U],
    *,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> list[U]:
    """并行映射列表元素 / Map list elements in parallel.

    使用 asyncio.gather 并发执行转换函数，保持结果顺序。
    Concurrently executes the transform function using
    asyncio.gather, preserving result order.

    Args:
        items: 待转换的元素序列 / The sequence of elements to
            transform.
        transform: 转换函数 / The transform function.
        concurrency: 最大并发数 / Maximum concurrency.

    Returns:
        按原始顺序排列的转换结果 / Transform results in the
        original order.
    """
    if not items:
        return []

    semaphore = asyncio.Semaphore(concurrency)

    async def _run(index: int, item: T) -> WorkerPoolResult[U]:
        """带信号量的任务执行 / Task execution with semaphore."""
        async with semaphore:
            result = transform(item)
            # 如果 transform 返回协程则 await / Await if coroutine
            if asyncio.iscoroutine(result):
                result = await result
            return WorkerPoolResult(index=index, result=result)

    results = await asyncio.gather(*(_run(i, item) for i, item in enumerate(items)))
    # 按索引排序保持顺序 / Sort by index to preserve order
    sorted_results = sorted(results, key=lambda r: r.index)
    return [r.result for r in sorted_results]
