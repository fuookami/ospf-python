"""远程二次求解器 / Remote quadratic solver.

提供远程二次规划求解能力。
Provides remote quadratic programming solving capability.
"""

from __future__ import annotations

import abc


class RemoteQuadraticSolver(abc.ABC):
    """远程二次求解器 / Remote quadratic solver.

    通过网络调用远程服务求解二次规划问题。
    Solves quadratic programming problems by calling
    remote services over the network.
    """

    @abc.abstractmethod
    def submit(self, model: object) -> str:
        """提交求解任务 / Submit solve task.

        Args:
            model: 二次规划模型 / The QP model.

        Returns:
            任务标识 / The task identifier.
        """
        ...

    @abc.abstractmethod
    def get_result(self, task_id: str) -> object:
        """获取求解结果 / Get solve result.

        Args:
            task_id: 任务标识 / The task identifier.

        Returns:
            求解结果 / The solve result.
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
