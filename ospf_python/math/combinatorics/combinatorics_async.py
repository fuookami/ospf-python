"""组合数学：异步组合与排列。

Combinatorics: Async combinations and permutations.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import TypeVar

from ospf_python.math.combinatorics.combinations import (
    combinations,
)
from ospf_python.math.combinatorics.permutations import (
    permutations,
)

T = TypeVar("T")


async def combinations_async(
    items: Sequence[T],
    k: int,
) -> list[list[T]]:
    """异步生成所有 k-组合。

    Asynchronously generate all k-combinations.

    将同步组合计算放入事件循环执行器中运行。
    Runs the synchronous combination computation
    in the event loop executor.

    Args:
        items: 候选元素序列。/ Candidate item sequence.
        k: 选取个数。/ Number of items to select.

    Returns:
        所有 k-组合列表。/ List of all k-combinations.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        combinations,
        items,
        k,
    )


async def permutations_async(
    items: Sequence[T],
    k: int,
) -> list[list[T]]:
    """异步生成所有 k-排列。

    Asynchronously generate all k-permutations.

    将同步排列计算放入事件循环执行器中运行。
    Runs the synchronous permutation computation
    in the event loop executor.

    Args:
        items: 候选元素序列。/ Candidate item sequence.
        k: 选取个数。/ Number of items to select.

    Returns:
        所有 k-排列列表。/ List of all k-permutations.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        permutations,
        items,
        k,
    )
