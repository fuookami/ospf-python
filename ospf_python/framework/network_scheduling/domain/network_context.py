"""网络上下文 / Network context.

定义网络调度的全局上下文信息。
Defines global context information for network scheduling.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkContext:
    """网络上下文 / Network context.

    携带网络调度过程中的全局配置与元数据。
    Carries global configuration and metadata during
    network scheduling.

    Attributes:
        network_key: 网络唯一标识 / Unique network identifier.
        name: 网络名称 / Network name.
        description: 网络描述 / Network description.
    """

    network_key: str
    name: str
    description: str = ""

    @staticmethod
    def create(
        *,
        network_key: str,
        name: str,
        description: str = "",
    ) -> NetworkContext:
        """工厂方法创建网络上下文 / Factory method to create a network context.

        Args:
            network_key: 网络唯一标识 / Unique network identifier.
            name: 网络名称 / Network name.
            description: 网络描述 / Network description.

        Returns:
            新的网络上下文实例 / New network context instance.
        """
        return NetworkContext(
            network_key=network_key,
            name=name,
            description=description,
        )
