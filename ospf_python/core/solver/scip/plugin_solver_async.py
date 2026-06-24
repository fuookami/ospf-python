"""SCIP 异步求解器包装器 / SCIP async solver wrapper.

为 SCIP 求解器提供异步求解能力。
Provides asynchronous solve capability for the SCIP
solver.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.core.solver.core_solver_async import (
    CoreSolverAsync,
)

if TYPE_CHECKING:
    from ospf_python.core.solver.output.solver_output import (
        SolverOutput,
    )
    from ospf_python.core.solver.solve_options import (
        SolveOptions,
    )
    from ospf_python.core.solver.solver import Solver


@dataclass(frozen=True)
class PluginSolverAsync(CoreSolverAsync):
    """SCIP 异步求解器包装器 / SCIP async solver wrapper.

    冻结数据类，使用线程池将同步求解器包装为异步接口。
    Frozen dataclass wrapping a synchronous solver as an
    async interface using a thread pool.

    Attributes:
        solver: 被包装的同步求解器 / The wrapped
            synchronous solver.
        executor: 线程池执行器 / Thread pool executor.
    """

    solver: Solver
    """被包装的同步求解器 / The wrapped synchronous solver."""

    executor: ThreadPoolExecutor = field(
        default_factory=lambda: ThreadPoolExecutor(
            max_workers=1,
        ),
    )
    """线程池执行器 / Thread pool executor."""

    async def solve_async(
        self,
        model: object,
        *,
        options: SolveOptions | None = None,
    ) -> SolverOutput:
        """异步求解模型 / Solve the model asynchronously.

        在线程池中执行同步求解，避免阻塞事件循环。
        Executes synchronous solve in a thread pool to
        avoid blocking the event loop.

        Args:
            model: 要求解的优化模型 / The optimization
                model.
            options: 求解选项 / Solve options.

        Returns:
            求解输出结果 / The solver output.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self.executor,
            lambda: self.solver.solve(
                model,
                options=options,
            ),
        )

    async def cancel(self) -> bool:
        """取消当前求解 / Cancel the current solve.

        注意：线程池中的求解无法被强制中断。
        Note: solves in the thread pool cannot be
        forcefully interrupted.

        Returns:
            始终返回 False / Always returns False.
        """
        return False
