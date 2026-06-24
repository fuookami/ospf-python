"""异步三维 BLA 求解器 / Async 3D BLA solver.

提供异步执行的三维 BLA 装箱求解。
Provides asynchronous 3D BLA bin packing solving.
"""

from __future__ import annotations

import abc


class Bpp3dBlaAsync(abc.ABC):
    """异步三维 BLA 求解器 / Async 3D BLA solver.

    异步执行三维自底向上左对齐装箱算法。
    Asynchronously executes the 3D bottom-up left-justified
    bin packing algorithm.
    """

    @abc.abstractmethod
    async def solve(self, items: tuple[object, ...]) -> object:
        """异步求解 / Async solve.

        Args:
            items: 待装箱物品 / Items to pack.

        Returns:
            装箱方案 / The packing solution.
        """
        ...

    @abc.abstractmethod
    async def cancel(self) -> None:
        """取消求解 / Cancel solving.

        请求取消正在执行的异步求解。
        Requests cancellation of the running async solve.
        """
        ...
