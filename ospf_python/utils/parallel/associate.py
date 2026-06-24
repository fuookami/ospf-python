"""并行关联操作 / Parallel associate operation.

对应 Kotlin 端 associateParallel。
Mirrors the Kotlin associateParallel.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from typing import TypeVar

from ospf_python.utils.parallel.common import WorkerPoolResult

# T: 输入类型 / Input type
T = TypeVar("T")

# K: 键类型 / Key type
K = TypeVar("K")

# V: 值类型 / Value type
V = TypeVar("V")

# 默认并发限制 / Default concurrency limit
_DEFAULT_CONCURRENCY = 8


async def associate_parallel(
    items: Sequence[T],
    transform: Callable[[T], tuple[K, V]],
    *,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> dict[K, V]:
    """并行构建字典 / Build a dictionary in parallel.

    并发执行转换函数，收集键值对构建字典。
    Concurrently executes the transform function and collects
    key-value pairs to build a dictionary.

    Args:
        items: 待转换的元素序列 / The sequence of elements to
            transform.
        transform: 返回键值对的转换函数 / Transform function
            returning a key-value pair.
        concurrency: 最大并发数 / Maximum concurrency.

    Returns:
        由转换结果构建的字典 / Dictionary built from transform
        results.
    """
    if not items:
        return {}

    semaphore = asyncio.Semaphore(concurrency)

    async def _run(index: int, item: T) -> WorkerPoolResult[tuple[K, V]]:
        """带信号量的任务执行 / Task execution with semaphore."""
        async with semaphore:
            result = transform(item)
            if asyncio.iscoroutine(result):
                result = await result
            return WorkerPoolResult(index=index, result=result)

    results = await asyncio.gather(*(_run(i, item) for i, item in enumerate(items)))
    return {r.result[0]: r.result[1] for r in results}
