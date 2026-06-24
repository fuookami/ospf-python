"""远程求解器 HTTP 传输插件 / Remote solver HTTP transport plugin.

定义 HTTP 传输的插件接口。
Defines the plugin interface for HTTP transport.
"""

from __future__ import annotations

import abc


class RemoteSolverHttpTransportPlugin(abc.ABC):
    """远程求解器 HTTP 传输插件 / Remote solver HTTP transport plugin.

    提供可插拔的 HTTP 传输实现。
    Provides a pluggable HTTP transport implementation.
    """

    @abc.abstractmethod
    def configure(self, config: dict[str, str]) -> None:
        """配置插件 / Configure plugin.

        Args:
            config: 配置参数 / The configuration parameters.
        """
        ...

    @abc.abstractmethod
    def is_configured(self) -> bool:
        """是否已配置 / Whether configured.

        Returns:
            已配置时返回 True / True when configured.
        """
        ...

    @abc.abstractmethod
    def shutdown(self) -> None:
        """关闭插件 / Shutdown plugin.

        释放插件占用的资源。
        Releases resources held by the plugin.
        """
        ...
