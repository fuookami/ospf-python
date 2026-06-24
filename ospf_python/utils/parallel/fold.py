"""并行折叠操作 / Parallel fold operation.

对应 Kotlin 端 foldParallel。
Mirrors the Kotlin foldParallel.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from typing import TypeVar

# T: 元素类型 / Element type
T = TypeVar("T")

# U: 累积值类型 / Accumulator type
U = TypeVar("U")

# 默认并发限制 / Default concurrency limit
_DEFAULT_CONCURRENCY = 8


async def fold_parallel(
    items: Sequence[T],
    initial: U,
    operation: Callable[[U, T], U],
    *,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> U:
    """并行折叠 / Fold in parallel.

    并发计算各元素的中间结果，然后顺序合并。
    并行阶段：每个元素独立计算中间值。
    顺序阶段：使用 operation 将中间值依次合并到初始值。
    Concurrently computes intermediate results for each element,
    then merges them sequentially. Parallel phase: each element
    independently computes an intermediate value. Sequential
    phase: merges intermediates into the initial value using
    operation.

    Args:
        items: 待折叠的元素序列 / The sequence of elements to fold.
        initial: 初始累积值 / The initial accumulator value.
        operation: 合并操作 / The merge operation.
        concurrency: 最大并发数 / Maximum concurrency.

    Returns:
        折叠后的最终值 / The final folded value.
    """
    if not items:
        return initial

    semaphore = asyncio.Semaphore(concurrency)

    async def _compute(index: int, item: T) -> tuple[int, T]:
        """带信号量的中间值计算 / Intermediate value computation
        with semaphore."""
        async with semaphore:
            return index, item

    # 并行阶段：计算中间结果（此处中间结果即元素本身）
    # Parallel phase: compute intermediates (here intermediates
    # are the items themselves)
    indexed = await asyncio.gather(*(_compute(i, item) for i, item in enumerate(items)))
    sorted_items = [item for _, item in sorted(indexed, key=lambda x: x[0])]

    # 顺序阶段：合并 / Sequential phase: merge
    accumulator = initial
    for item in sorted_items:
        result = operation(accumulator, item)
        if asyncio.iscoroutine(result):
            result = await result
        accumulator = result
    return accumulator
