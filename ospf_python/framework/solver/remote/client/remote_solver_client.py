"""远程求解器客户端 / Remote solver client.

提供远程求解器的统一客户端接口。
Provides a unified client interface for remote solvers.
"""

from __future__ import annotations

import abc
from typing import Any


class RemoteSolverClient(abc.ABC):
    """远程求解器客户端 / Remote solver client.

    封装远程求解器的调用逻辑。
    Encapsulates the calling logic for remote solvers.
    """

    @abc.abstractmethod
    def submit_solve(
        self,
        model_data: bytes,
        *,
        solver_type: str,
    ) -> str:
        """提交求解 / Submit solve.

        Args:
            model_data: 模型数据 / The model data.
            solver_type: 求解器类型 / The solver type.

        Returns:
            任务标识 / The task identifier.
        """
        ...

    @abc.abstractmethod
    def poll_status(self, task_id: str) -> str:
        """轮询状态 / Poll status.

        Args:
            task_id: 任务标识 / The task identifier.

        Returns:
            任务状态 / The task status.
        """
        ...

    @abc.abstractmethod
    def fetch_result(self, task_id: str) -> dict[str, Any]:
        """获取结果 / Fetch result.

        Args:
            task_id: 任务标识 / The task identifier.

        Returns:
            求解结果字典 / The solve result dictionary.
        """
        ...
