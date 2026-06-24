"""异步计算守卫 / Async computation guard.

对应 Kotlin 端 Async<T>。
提供带超时保护的异步计算包装器。
Mirrors the Kotlin Async<T>. Provides a wrapper for async
computation with timeout guard.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, Generic, TypeVar

# T: 计算结果类型 / Computation result type
T = TypeVar("T")


class Async(Generic[T]):
    """异步计算守卫 / Async computation guard.

    包装异步计算，提供超时控制和生命周期管理。
    Wraps an async computation, providing timeout control
    and lifecycle management.

    Attributes:
        _computation: 异步计算函数 / The async computation callable.
        _timeout: 超时时间（秒） / Timeout in seconds.
        _task: 底层异步任务 / The underlying async task.
    """

    def __init__(
        self,
        computation: Callable[[], Coroutine[Any, Any, T]],
        *,
        timeout: float | None = None,
    ) -> None:
        """初始化异步守卫 / Initialize the async guard.

        Args:
            computation: 异步计算函数 / Async computation callable.
            timeout: 超时秒数，None 表示无超时 / Timeout in seconds,
                None means no timeout.
        """
        self._computation = computation
        self._timeout = timeout
        self._task: asyncio.Task[T] | None = None

    async def run(self) -> T:
        """执行异步计算 / Execute the async computation.

        启动计算并在超时时取消。
        Starts the computation and cancels on timeout.

        Returns:
            计算结果 / The computation result.
        """
        self._task = asyncio.create_task(self._computation())

        if self._timeout is not None:
            try:
                return await asyncio.wait_for(self._task, timeout=self._timeout)
            except TimeoutError:
                self._task.cancel()
                return await self._task  # 重新抛出 CancelledError
        return await self._task

    def cancel(self) -> None:
        """取消异步计算 / Cancel the async computation."""
        if self._task is not None and not self._task.done():
            self._task.cancel()

    @property
    def is_done(self) -> bool:
        """检查计算是否已完成 / Check if the computation is done."""
        if self._task is None:
            return False
        return self._task.done()
