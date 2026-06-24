"""远程求解器 HTTP 客户端 / Remote solver HTTP client.

基于 HTTP 的远程求解器客户端。
HTTP-based remote solver client.
"""

from __future__ import annotations

import abc
from typing import Any


class RemoteSolverHttpClient(abc.ABC):
    """远程求解器 HTTP 客户端 / Remote solver HTTP client.

    通过 HTTP 协议与远程求解器服务交互。
    Interacts with remote solver services via HTTP.
    """

    @abc.abstractmethod
    def post_model(
        self,
        endpoint: str,
        model_data: bytes,
    ) -> dict[str, Any]:
        """发送模型 / Post model.

        Args:
            endpoint: 服务端点 / The service endpoint.
            model_data: 模型数据 / The model data.

        Returns:
            响应数据 / The response data.
        """
        ...

    @abc.abstractmethod
    def get_status(
        self,
        endpoint: str,
        task_id: str,
    ) -> dict[str, Any]:
        """获取状态 / Get status.

        Args:
            endpoint: 服务端点 / The service endpoint.
            task_id: 任务标识 / The task identifier.

        Returns:
            状态数据 / The status data.
        """
        ...

    @abc.abstractmethod
    def get_result(
        self,
        endpoint: str,
        task_id: str,
    ) -> bytes:
        """获取结果 / Get result.

        Args:
            endpoint: 服务端点 / The service endpoint.
            task_id: 任务标识 / The task identifier.

        Returns:
            结果数据 / The result data.
        """
        ...
