"""异步求解器接口 / Async solver interface.

定义异步求解操作的接口。
Defines the interface for asynchronous solve operations.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.solver.output.solver_output import (
        SolverOutput,
    )
    from ospf_python.core.solver.solve_options import SolveOptions


class CoreSolverAsync(abc.ABC):
    """异步求解器接口 / Async solver interface.

    提供异步求解能力，允许在不阻塞主线程的情况下
    执行求解操作。
    Provides asynchronous solve capability, allowing solve
    operations without blocking the main thread.
    """

    @abc.abstractmethod
    async def solve_async(
        self,
        model: object,
        *,
        options: SolveOptions | None = None,
    ) -> SolverOutput:
        """异步求解模型 / Solve the model asynchronously.

        Args:
            model: 要求解的优化模型 / The optimization model
                to solve.
            options: 求解选项 / Solve options.

        Returns:
            求解输出结果 / The solver output.
        """
        ...

    @abc.abstractmethod
    async def cancel(self) -> bool:
        """取消当前求解 / Cancel the current solve.

        Returns:
            成功取消返回 True / True if cancellation
            was successful.
        """
        ...
