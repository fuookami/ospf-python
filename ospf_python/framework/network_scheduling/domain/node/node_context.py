"""节点上下文 / Node context.

定义节点操作的上下文信息。
Defines context information for node operations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NodeContext:
    """节点上下文 / Node context.

    携带节点查询或操作时的附加上下文。
    Carries additional context during node queries
    or operations.

    Attributes:
        network_key: 所属网络标识 / Owning network identifier.
        filter_type: 按类型过滤（空字符串不过滤）/
            Filter by type (empty string means no filter).
        max_results: 最大返回数量 / Maximum number of results.
    """

    network_key: str
    filter_type: str = ""
    max_results: int = 0

    @staticmethod
    def create(
        *,
        network_key: str,
        filter_type: str = "",
        max_results: int = 0,
    ) -> NodeContext:
        """工厂方法创建节点上下文 / Factory method to create a node context.

        Args:
            network_key: 所属网络标识 / Owning network identifier.
            filter_type: 按类型过滤 / Filter by type.
            max_results: 最大返回数量 / Maximum results.

        Returns:
            新的节点上下文实例 / New node context instance.
        """
        return NodeContext(
            network_key=network_key,
            filter_type=filter_type,
            max_results=max_results,
        )
