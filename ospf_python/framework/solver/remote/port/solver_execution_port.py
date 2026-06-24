"""求解器执行端口 / Solver execution port.

定义求解器执行的抽象端口接口。
Defines the abstract port interface for solver execution.
"""

from __future__ import annotations

import abc
from typing import Any


class SolverExecutionPort(abc.ABC):
    """求解器执行端口 / Solver execution port.

    提供求解器任务提交和结果获取的抽象接口。
    Provides abstract interface for solver task submission
    and result retrieval.
    """

    @abc.abstractmethod
    def submit(
        self,
        model_data: bytes,
        *,
        solver_type: str,
        options: dict[str, Any] | None = None,
    ) -> str:
        """提交求解任务 / Submit solve task.

        Args:
            model_data: 模型数据 / The model data.
            solver_type: 求解器类型 / The solver type.
            options: 求解选项 / The solve options.

        Returns:
            任务标识 / The task identifier.
        """
        ...

    @abc.abstractmethod
    def poll(self, task_id: str) -> str:
        """轮询任务状态 / Poll task status.

        Args:
            task_id: 任务标识 / The task identifier.

        Returns:
            任务状态 / The task status.
        """
        ...

    @abc.abstractmethod
    def retrieve(self, task_id: str) -> bytes:
        """获取任务结果 / Retrieve task result.

        Args:
            task_id: 任务标识 / The task identifier.

        Returns:
            结果数据 / The result data.
        """
        ...

    @abc.abstractmethod
    def cancel(self, task_id: str) -> bool:
        """取消任务 / Cancel task.

        Args:
            task_id: 任务标识 / The task identifier.

        Returns:
            取消成功返回 True / True if cancellation succeeded.
        """
        ...
