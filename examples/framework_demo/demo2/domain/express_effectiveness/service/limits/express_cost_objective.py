"""快递成本优化目标。

Express cost objective for minimizing handling costs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...model.express_priority import ExpressPriority


@dataclass(frozen=True)
class ExpressCostShipment:
    """成本计算快件信息。

    Shipment data needed for cost computation.

    Attributes:
        shipment_id: 快件标识 / Shipment identifier
        priority: 配送优先级 / Delivery priority
        weight: 快件重量（千克）/ Shipment weight (kg)
        distance: 配送距离（千米）/ Delivery distance (km)
    """

    shipment_id: str
    priority: ExpressPriority
    weight: float
    distance: float


@dataclass(frozen=True)
class ExpressCostObjective:
    """快递成本优化目标。

    Minimizes total express handling cost by computing per-shipment
    costs based on priority, weight, and distance.

    Attributes:
        base_rate: 基础费率（元/千克·公里）/ Base rate (CNY per kg*km)
        weight: 目标权重 / Objective weight in overall scoring
        budget: 预算上限（元）/ Budget ceiling (CNY)
    """

    base_rate: float
    weight: float
    budget: float

    def compute_cost(self, shipment: ExpressCostShipment) -> float:
        """计算单个快件的处理成本。

        Args:
            shipment: 快件信息 / Shipment data

        Returns:
            float: 处理成本（元）/ Handling cost (CNY)
        """
        multiplier = shipment.priority.cost_multiplier()
        return self.base_rate * shipment.weight * shipment.distance * multiplier

    def compute_total(
        self,
        shipments: tuple[ExpressCostShipment, ...],
    ) -> tuple[float, float]:
        """计算总成本和得分。

        Args:
            shipments: 所有快件 / All shipments

        Returns:
            tuple: (总成本, 加权得分) / (total cost, weighted score)
        """
        total_cost = sum(self.compute_cost(s) for s in shipments)
        if self.budget <= 0.0:
            score = 0.0
        else:
            ratio = total_cost / self.budget
            score = max(0.0, 1.0 - ratio) * self.weight
        return (total_cost, score)

    def cost_breakdown(
        self,
        shipments: tuple[ExpressCostShipment, ...],
    ) -> dict[str, float]:
        """按优先级分解成本。

        Args:
            shipments: 所有快件 / All shipments

        Returns:
            dict: 各优先级成本 / Cost by priority level
        """
        breakdown: dict[str, float] = {}
        for s in shipments:
            label = s.priority.label_zh()
            cost = self.compute_cost(s)
            breakdown[label] = breakdown.get(label, 0.0) + cost
        return breakdown

    def is_within_budget(
        self,
        shipments: tuple[ExpressCostShipment, ...],
    ) -> bool:
        """判断是否在预算内。

        Args:
            shipments: 所有快件 / All shipments

        Returns:
            bool: 是否在预算内 / Whether within budget
        """
        total = sum(self.compute_cost(s) for s in shipments)
        return total <= self.budget
