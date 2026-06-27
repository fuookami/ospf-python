"""需求模型 / Demand model.

定义网络中源到汇的流量需求。
Defines flow demand from source to sink in a network.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Demand:
    """流量需求 / Flow demand.

    表示从源节点到汇节点的流量需求，包含需求量和优先级。
    Represents a flow requirement from a source node to a
    sink node, including the amount and priority.

    Attributes:
        demand_key: 需求唯一标识 / Unique demand identifier.
        source_key: 源节点标识 / Source node identifier.
        sink_key: 汇节点标识 / Sink node identifier.
        amount: 需求量 / Demand amount.
        priority: 优先级（数值越大越优先）/ Priority
            (higher = more preferred).
    """

    demand_key: str
    source_key: str
    sink_key: str
    amount: float
    priority: int = 0

    @staticmethod
    def create(
        *,
        demand_key: str,
        source_key: str,
        sink_key: str,
        amount: float,
        priority: int = 0,
    ) -> Demand:
        """工厂方法创建需求 / Factory method to create a demand.

        Args:
            demand_key: 需求唯一标识 / Unique demand identifier.
            source_key: 源节点标识 / Source node identifier.
            sink_key: 汇节点标识 / Sink node identifier.
            amount: 需求量 / Demand amount.
            priority: 优先级 / Priority.

        Returns:
            新的需求实例 / New demand instance.
        """
        return Demand(
            demand_key=demand_key,
            source_key=source_key,
            sink_key=sink_key,
            amount=amount,
            priority=priority,
        )

    @property
    def is_satisfied(self) -> bool:
        """需求是否已满足 / Whether the demand is satisfied.

        需求量为零或负值时视为已满足。
        A demand with zero or negative amount is
        considered satisfied.

        Returns:
            是否已满足 / Whether satisfied.
        """
        return self.amount <= 0.0

    def with_amount(self, amount: float) -> Demand:
        """创建不同需求量的需求 / Create demand with different amount.

        Args:
            amount: 新需求量 / New demand amount.

        Returns:
            新的需求实例 / New demand instance.
        """
        return Demand(
            demand_key=self.demand_key,
            source_key=self.source_key,
            sink_key=self.sink_key,
            amount=amount,
            priority=self.priority,
        )

    def is_satisfied_by(self, flow_amount: float) -> bool:
        """检查给定流量是否满足需求。

        Check if a given flow amount satisfies this demand.

        Args:
            flow_amount: 已分配的流量 / Allocated flow amount.

        Returns:
            是否满足 / Whether satisfied.
        """
        return flow_amount >= self.amount
