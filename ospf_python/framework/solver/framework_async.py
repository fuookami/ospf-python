"""框架异步工具 / Framework async utilities.

提供框架层的异步操作工具函数。
Provides async utility functions for the framework layer.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


async def run_with_timeout(
    coro: Coroutine[Any, Any, T],
    *,
    timeout_seconds: float,
) -> T:
    """带超时运行协程 / Run coroutine with timeout.

    Args:
        coro: 要执行的协程 / The coroutine to execute.
        timeout_seconds: 超时秒数 / Timeout in seconds.

    Returns:
        协程返回值 / The coroutine return value.
    """
    return await asyncio.wait_for(coro, timeout=timeout_seconds)


async def gather_with_limit(
    *coros: Coroutine[Any, Any, Any],
    limit: int = 10,
) -> list[Any]:
    """有限并发执行协程 / Gather coroutines with concurrency limit.

    Args:
        coros: 要执行的协程们 / The coroutines to execute.
        limit: 最大并发数 / Maximum concurrency.

    Returns:
        各协程的返回值列表 / List of coroutine return values.
    """
    semaphore = asyncio.Semaphore(limit)

    async def _wrapper(
        coro: Coroutine[Any, Any, Any],
    ) -> Any:
        async with semaphore:
            return await coro

    return await asyncio.gather(
        *(_wrapper(c) for c in coros),
    )
