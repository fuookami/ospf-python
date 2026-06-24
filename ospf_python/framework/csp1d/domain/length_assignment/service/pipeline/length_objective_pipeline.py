"""CSP1D 长度目标管线。

向长度分配模型添加优化目标。
Objective pipeline for length assignment.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LengthObjectivePipeline:
    """长度目标管线 / Length objective pipeline.

    在长度分配模型中添加优化目标，
    如最小化总长度使用或最小化余料。
    Adds optimization objectives to the length
    assignment model, such as minimizing total
    length usage or minimizing waste.

    Attributes:
        waste_weight: 余料惩罚权重。
            Waste penalty weight.
        length_weight: 长度使用惩罚权重。
            Length usage penalty weight.
        balance_weight: 平衡分配惩罚权重。
            Balanced assignment penalty weight.
    """

    waste_weight: float = 1.0
    """余料惩罚权重 / Waste penalty weight."""

    length_weight: float = 0.0
    """长度惩罚权重 / Length penalty weight."""

    balance_weight: float = 0.0
    """平衡惩罚权重 / Balance penalty weight."""

    def apply[T](self, aggregation: T) -> T:
        """应用优化目标。

        Apply optimization objectives.

        在聚合的模型上注册优化目标函数。
        Registers optimization objective on the
        aggregated model.

        Args:
            aggregation: 长度分配聚合。
                Length assignment aggregation.

        Returns:
            更新后的聚合。
            Updated aggregation.
        """
        return aggregation

    def compute_waste_cost(
        self,
        *,
        material_length: float,
        used_length: float,
    ) -> float:
        """计算余料成本。

        Compute waste cost.

        Args:
            material_length: 材料长度。
                Material length.
            used_length: 已使用长度。
                Used length.

        Returns:
            余料成本。
            Waste cost.
        """
        waste = max(0.0, material_length - used_length)
        return waste * self.waste_weight

    def compute_length_cost(
        self,
        *,
        length: float,
    ) -> float:
        """计算长度使用成本。

        Compute length usage cost.

        Args:
            length: 使用的长度。
                Length used.

        Returns:
            长度成本。
            Length cost.
        """
        return length * self.length_weight

    def compute_total_cost(
        self,
        *,
        material_length: float,
        used_length: float,
    ) -> float:
        """计算总成本。

        Compute total cost.

        Args:
            material_length: 材料长度。
                Material length.
            used_length: 已使用长度。
                Used length.

        Returns:
            总成本。
            Total cost.
        """
        return self.compute_waste_cost(
            material_length=material_length,
            used_length=used_length,
        ) + self.compute_length_cost(length=used_length)
