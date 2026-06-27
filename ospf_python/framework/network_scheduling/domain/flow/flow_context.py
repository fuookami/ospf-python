"""流上下文 / Flow context.

定义流操作的上下文信息。
Defines context information for flow operations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FlowContext:
    """流上下文 / Flow context.

    携带流查询或操作时的附加上下文。
    Carries additional context during flow queries
    or operations.

    Attributes:
        network_key: 所属网络标识 / Owning network identifier.
        edge_key: 按边过滤（空字符串不过滤）/
            Filter by edge (empty = no filter).
        min_amount: 最小流量阈值 / Minimum flow threshold.
        max_amount: 最大流量限制 / Maximum flow limit.
    """

    network_key: str
    edge_key: str = ""
    min_amount: float = 0.0
    max_amount: float = float("inf")

    @staticmethod
    def create(
        *,
        network_key: str,
        edge_key: str = "",
        min_amount: float = 0.0,
        max_amount: float = float("inf"),
    ) -> FlowContext:
        """工厂方法创建流上下文 / Factory method to create a flow context.

        Args:
            network_key: 所属网络标识 / Owning network identifier.
            edge_key: 按边过滤 / Filter by edge.
            min_amount: 最小流量阈值 / Minimum flow threshold.
            max_amount: 最大流量限制 / Maximum flow limit.

        Returns:
            新的流上下文实例 / New flow context instance.
        """
        return FlowContext(
            network_key=network_key,
            edge_key=edge_key,
            min_amount=min_amount,
            max_amount=max_amount,
        )
