"""异步块装载求解器 / Async block loading solver.

提供异步执行的块装载求解。
Provides asynchronous block loading solving.
"""

from __future__ import annotations

import abc


class Bpp3dBlockLoadingAsync(abc.ABC):
    """异步块装载求解器 / Async block loading solver.

    异步执行块装载算法。
    Asynchronously executes block loading algorithms.
    """

    @abc.abstractmethod
    async def solve(self, blocks: tuple[object, ...]) -> object:
        """异步求解 / Async solve.

        Args:
            blocks: 待装载块 / Blocks to load.

        Returns:
            装载方案 / The loading solution.
        """
        ...

    @abc.abstractmethod
    async def cancel(self) -> None:
        """取消求解 / Cancel solving.

        请求取消正在执行的异步求解。
        Requests cancellation of the running async solve.
        """
        ...
