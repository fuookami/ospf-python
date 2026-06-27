"""边上下文 / Edge context.

定义边操作的上下文信息。
Defines context information for edge operations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EdgeContext:
    """边上下文 / Edge context.

    携带边查询或操作时的附加上下文。
    Carries additional context during edge queries
    or operations.

    Attributes:
        network_key: 所属网络标识 / Owning network identifier.
        from_node_key: 按起始节点过滤（空字符串不过滤）/
            Filter by source node (empty = no filter).
        to_node_key: 按终止节点过滤（空字符串不过滤）/
            Filter by target node (empty = no filter).
        max_cost: 最大单位代价限制 / Maximum unit cost limit.
    """

    network_key: str
    from_node_key: str = ""
    to_node_key: str = ""
    max_cost: float = float("inf")

    @staticmethod
    def create(
        *,
        network_key: str,
        from_node_key: str = "",
        to_node_key: str = "",
        max_cost: float = float("inf"),
    ) -> EdgeContext:
        """工厂方法创建边上下文 / Factory method to create an edge context.

        Args:
            network_key: 所属网络标识 / Owning network identifier.
            from_node_key: 按起始节点过滤 / Filter by source node.
            to_node_key: 按终止节点过滤 / Filter by target node.
            max_cost: 最大单位代价限制 / Maximum unit cost limit.

        Returns:
            新的边上下文实例 / New edge context instance.
        """
        return EdgeContext(
            network_key=network_key,
            from_node_key=from_node_key,
            to_node_key=to_node_key,
            max_cost=max_cost,
        )
