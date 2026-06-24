"""网络响应 / Network response.

定义网络请求的响应数据结构。
Defines the data structure for network responses.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Response:
    """网络响应 / Network response.

    封装 HTTP 响应的状态码、响应体和响应头。
    Wraps HTTP response status code, body, and headers.

    Attributes:
        status: HTTP 状态码 / The HTTP status code.
        body: 响应体 / The response body.
        headers: 响应头 / The response headers.
    """

    status: int
    body: str
    headers: dict[str, str]
