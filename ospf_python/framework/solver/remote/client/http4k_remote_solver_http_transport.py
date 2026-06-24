"""HTTP4K 远程求解器传输 / HTTP4K remote solver transport.

基于 HTTP 的远程求解器传输实现。
HTTP-based transport implementation for remote solvers.
"""

from __future__ import annotations

import abc
from typing import Any


class Http4kRemoteSolverHttpTransport(abc.ABC):
    """HTTP4K 远程求解器传输 / HTTP4K remote solver HTTP transport.

    通过 HTTP 协议与远程求解器通信。
    Communicates with remote solvers via HTTP protocol.
    """

    @abc.abstractmethod
    def send_request(
        self,
        url: str,
        method: str,
        *,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """发送请求 / Send request.

        Args:
            url: 请求地址 / The request URL.
            method: HTTP 方法 / The HTTP method.
            body: 请求体 / The request body.
            headers: 请求头 / The request headers.

        Returns:
            响应数据 / The response data.
        """
        ...

    @abc.abstractmethod
    def is_available(self) -> bool:
        """是否可用 / Whether available.

        Returns:
            传输通道可用时返回 True /
            True when the transport channel is available.
        """
        ...
