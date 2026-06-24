"""通道守卫 / Channel guard.

对应 Kotlin 端 ChannelGuard。
提供有界通道访问的信号量/锁包装器。
Mirrors the Kotlin ChannelGuard. Provides a semaphore/lock
wrapper for bounded channel access.
"""

from __future__ import annotations

import asyncio
from typing import Generic, TypeVar

# T: 通道中传输的值类型 / Value type transmitted in the channel
T = TypeVar("T")


class ChannelGuard(Generic[T]):
    """通道守卫 / Channel guard.

    使用信号量控制对有界通道的并发访问，确保不超过指定容量。
    Uses a semaphore to control concurrent access to a bounded
    channel, ensuring the capacity is not exceeded.

    Attributes:
        _capacity: 通道容量 / The channel capacity.
        _semaphore: 并发控制信号量 / Concurrency control semaphore.
        _channel: 底层异步队列 / The underlying async queue.
    """

    def __init__(self, capacity: int) -> None:
        """初始化通道守卫 / Initialize the channel guard.

        Args:
            capacity: 通道容量 / The channel capacity.
        """
        self._capacity: int = capacity
        self._semaphore: asyncio.Semaphore = asyncio.Semaphore(capacity)
        self._channel: asyncio.Queue[T] = asyncio.Queue(maxsize=capacity)

    async def send(self, value: T) -> None:
        """发送值到通道 / Send a value to the channel.

        获取信号量许可后将值放入通道。
        Acquires a semaphore permit before putting the value
        into the channel.

        Args:
            value: 待发送的值 / The value to send.
        """
        await self._semaphore.acquire()
        await self._channel.put(value)

    async def receive(self) -> T:
        """从通道接收值 / Receive a value from the channel.

        从通道取出值后释放信号量许可。
        Gets a value from the channel and releases the
        semaphore permit.

        Returns:
            接收到的值 / The received value.
        """
        value = await self._channel.get()
        self._semaphore.release()
        return value

    @property
    def capacity(self) -> int:
        """获取通道容量 / Get the channel capacity."""
        return self._capacity

    @property
    def size(self) -> int:
        """获取当前队列大小 / Get the current queue size."""
        return self._channel.qsize()
