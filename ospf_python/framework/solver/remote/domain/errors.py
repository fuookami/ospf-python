"""远程求解器错误类型 / Remote solver error types.

定义远程求解器域的错误类型。
Defines error types for the remote solver domain.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RemoteSolverError:
    """远程求解器错误 / Remote solver error.

    表示远程求解过程中发生的错误。
    Represents an error that occurred during remote solving.

    Attributes:
        code: 错误码 / The error code.
        message: 错误信息 / The error message.
        task_id: 关联的任务标识 / The associated task identifier.
    """

    code: int
    message: str
    task_id: str = ""


@dataclass(frozen=True)
class ConnectionError:
    """连接错误 / Connection error.

    表示与远程服务的连接失败。
    Represents a connection failure to the remote service.

    Attributes:
        url: 目标 URL / The target URL.
        message: 错误信息 / The error message.
    """

    url: str
    message: str


@dataclass(frozen=True)
class TimeoutError:
    """超时错误 / Timeout error.

    表示远程操作超时。
    Represents a timeout of a remote operation.

    Attributes:
        timeout_seconds: 超时秒数 / The timeout in seconds.
        operation: 超时操作 / The timed out operation.
    """

    timeout_seconds: float
    operation: str
