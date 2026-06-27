"""流模型 / Flow model.

定义网络中边上流量的核心数据结构。
Defines the core data structure for flow on a network edge.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Flow:
    """边上的流量 / Flow on an edge.

    表示某条边上的流量分配，包含流量值和代价。
    Represents a flow allocation on an edge, containing
    the flow amount and associated cost.

    Attributes:
        flow_key: 流唯一标识 / Unique flow identifier.
        edge_key: 所属边标识 / Owning edge identifier.
        amount: 流量值 / Flow amount.
        cost: 该流量的总代价 / Total cost of this flow.
    """

    flow_key: str
    edge_key: str
    amount: float
    cost: float = 0.0

    @staticmethod
    def create(
        *,
        flow_key: str,
        edge_key: str,
        amount: float,
        cost: float = 0.0,
    ) -> Flow:
        """工厂方法创建流 / Factory method to create a flow.

        Args:
            flow_key: 流唯一标识 / Unique flow identifier.
            edge_key: 所属边标识 / Owning edge identifier.
            amount: 流量值 / Flow amount.
            cost: 该流量的总代价 / Total cost of this flow.

        Returns:
            新的流实例 / New flow instance.
        """
        return Flow(
            flow_key=flow_key,
            edge_key=edge_key,
            amount=amount,
            cost=cost,
        )

    def is_feasible(self, capacity: float) -> bool:
        """检查流量是否在容量限制内。

        Check if the flow amount is within capacity limits.

        Args:
            capacity: 边容量 / Edge capacity.

        Returns:
            是否可行 / Whether feasible.
        """
        if capacity == float("inf"):
            return self.amount >= 0.0
        return 0.0 <= self.amount <= capacity

    def with_amount(self, amount: float) -> Flow:
        """创建不同流量值的流 / Create flow with different amount.

        代价按比例缩放。
        Cost is scaled proportionally.

        Args:
            amount: 新流量值 / New flow amount.

        Returns:
            新的流实例 / New flow instance.
        """
        new_cost = 0.0 if self.amount == 0.0 else self.cost * (amount / self.amount)
        return Flow(
            flow_key=self.flow_key,
            edge_key=self.edge_key,
            amount=amount,
            cost=new_cost,
        )

    def residual_capacity(self, edge_capacity: float) -> float:
        """计算剩余容量 / Calculate residual capacity.

        返回边容量与当前流量的差值。
        Returns the difference between edge capacity
        and current flow.

        Args:
            edge_capacity: 边的总容量 / Total edge capacity.

        Returns:
            剩余可用容量 / Residual available capacity.
        """
        if edge_capacity == float("inf"):
            return float("inf")
        return max(0.0, edge_capacity - self.amount)
