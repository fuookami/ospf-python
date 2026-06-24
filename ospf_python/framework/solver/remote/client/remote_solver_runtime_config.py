"""远程求解器运行时配置 / Remote solver runtime config.

定义远程求解器的运行时配置。
Defines runtime configuration for remote solvers.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RemoteSolverRuntimeConfig:
    """远程求解器运行时配置 / Remote solver runtime config.

    包含远程求解器连接和行为的配置参数。
    Contains configuration parameters for remote solver
    connection and behavior.

    Attributes:
        base_url: 服务基础 URL / The service base URL.
        timeout_seconds: 请求超时秒数 / Request timeout in seconds.
        max_retries: 最大重试次数 / Maximum retry count.
        api_key: API 密钥 / The API key.
    """

    base_url: str
    timeout_seconds: float = 300.0
    max_retries: int = 3
    api_key: str = ""
