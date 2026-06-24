"""CSP1D 余料聚合。

聚合余料最小化领域的多个模型组件。
Aggregation for waste minimization domain.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.framework.csp1d.domain.wasting_minimization.model.waste_model import (
    WasteModel,
)


@dataclass(frozen=True)
class WasteAggregation:
    """余料聚合 / Waste aggregation.

    聚合余料模型和相关配置，协调余料最小化
    领域内的组件注册和交互。
    Aggregates waste model and related config,
    coordinating component registration and
    interaction within waste minimization domain.

    Attributes:
        model: 余料模型。
            Waste model.
        target_waste_ratio: 目标余料率。
            Target waste ratio.
        penalty_weight: 余料惩罚权重。
            Waste penalty weight.
    """

    model: WasteModel = field(
        default_factory=WasteModel,
    )
    """余料模型 / Waste model."""

    target_waste_ratio: float = 0.05
    """目标余料率 / Target waste ratio."""

    penalty_weight: float = 1.0
    """惩罚权重 / Penalty weight."""

    @staticmethod
    def create(
        *,
        material_lengths: tuple[float, ...],
        target_waste_ratio: float = 0.05,
    ) -> WasteAggregation:
        """创建余料聚合。

        Create waste aggregation.

        Args:
            material_lengths: 可用材料长度。
                Available material lengths.
            target_waste_ratio: 目标余料率，默认 0.05。
                Target waste ratio, default 0.05.

        Returns:
            聚合实例。
            Aggregation instance.
        """
        model = WasteModel.create(
            material_lengths=material_lengths,
        )
        return WasteAggregation(
            model=model,
            target_waste_ratio=target_waste_ratio,
        )

    def with_waste_data(
        self,
        *,
        waste_data: tuple[tuple[str, float], ...],
    ) -> WasteAggregation:
        """创建包含余料数据的新聚合。

        Create new aggregation with waste data.

        Args:
            waste_data: 余料数据。
                Waste data.

        Returns:
            新聚合实例。
            New aggregation instance.
        """
        new_model = self.model.with_waste_data(
            waste_data=waste_data,
        )
        return WasteAggregation(
            model=new_model,
            target_waste_ratio=self.target_waste_ratio,
            penalty_weight=self.penalty_weight,
        )

    @property
    def total_waste(self) -> float:
        """获取总余料量。

        Get total waste amount.

        Returns:
            总余料量。
            Total waste amount.
        """
        return self.model.total_waste

    @property
    def average_waste(self) -> float:
        """获取平均余料。

        Get average waste.

        Returns:
            平均余料量。
            Average waste amount.
        """
        return self.model.average_waste

    def is_below_target(
        self,
        *,
        actual_ratio: float,
    ) -> bool:
        """检查实际余料率是否低于目标。

        Check if actual waste ratio is below target.

        Args:
            actual_ratio: 实际余料率。
                Actual waste ratio.

        Returns:
            低于目标返回 True / True if below target.
        """
        return actual_ratio <= self.target_waste_ratio
