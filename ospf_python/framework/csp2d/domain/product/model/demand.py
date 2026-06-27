"""产品需求模型 / Product demand model.

CSP2D 中的产品需求定义。
Product demand definition in CSP2D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Demand:
    """产品需求 / Product demand.

    描述对某种形状产品的需求，包括数量和优先级。
    Describes demand for a shape product,
    including quantity and priority.

    Attributes:
        demand_key: 需求唯一键 / Demand unique key.
        shape_key: 关联形状键 / Associated shape key.
        quantity: 需求数量 / Demand quantity.
        priority: 需求优先级（越大越重要） /
            Demand priority (higher = more important).
    """

    demand_key: str
    """需求唯一键 / Demand unique key."""

    shape_key: str
    """关联形状键 / Associated shape key."""

    quantity: int
    """需求数量 / Demand quantity."""

    priority: int
    """需求优先级 / Demand priority."""

    @staticmethod
    def create(
        *,
        demand_key: str,
        shape_key: str,
        quantity: int,
        priority: int = 0,
    ) -> Demand:
        """创建需求 / Create demand.

        Args:
            demand_key: 需求唯一键 / Demand unique key.
            shape_key: 关联形状键 / Associated shape key.
            quantity: 需求数量 / Demand quantity.
            priority: 需求优先级，默认 0 /
                Demand priority, default 0.

        Returns:
            需求实例 / Demand instance.
        """
        return Demand(
            demand_key=demand_key,
            shape_key=shape_key,
            quantity=quantity,
            priority=priority,
        )

    def is_satisfied_by(self, fulfilled: int) -> bool:
        """检查是否已被满足 / Check if satisfied by fulfilled count.

        Args:
            fulfilled: 已完成数量 / Fulfilled count.

        Returns:
            是否已满足需求 / Whether demand is satisfied.
        """
        return fulfilled >= self.quantity

    def remaining(self, fulfilled: int) -> int:
        """计算剩余需求数量 / Calculate remaining demand.

        Args:
            fulfilled: 已完成数量 / Fulfilled count.

        Returns:
            剩余需求量（最小为 0） / Remaining demand (min 0).
        """
        return max(0, self.quantity - fulfilled)

    def with_quantity(self, qty: int) -> Demand:
        """创建指定数量的新需求 / Create new demand with given quantity.

        保持其他字段不变，返回新实例。
        Keeps other fields unchanged, returns new instance.

        Args:
            qty: 新需求量 / New quantity.

        Returns:
            新需求实例 / New demand instance.
        """
        return Demand(
            demand_key=self.demand_key,
            shape_key=self.shape_key,
            quantity=qty,
            priority=self.priority,
        )
