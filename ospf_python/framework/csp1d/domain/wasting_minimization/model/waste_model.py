"""CSP1D 余料模型。

管理余料最小化优化模型的变量和约束。
Model for waste minimization optimization.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WasteModel:
    """余料模型 / Waste model.

    管理余料最小化问题中的决策变量和约束。
    用于在列生成过程中评估和优化余料。
    Manages decision variables and constraints in
    the waste minimization problem. Used to evaluate
    and optimize waste during column generation.

    Attributes:
        material_lengths: 可用材料长度。
            Available material lengths.
        waste_per_plan: 每个切割方案的余料。
            Waste per cutting plan.
        total_waste: 总余料量。
            Total waste amount.
        precision: 数值精度。
            Numerical precision.
    """

    material_lengths: tuple[float, ...] = ()
    """可用材料长度 / Available material lengths."""

    waste_per_plan: tuple[tuple[str, float], ...] = ()
    """每方案余料 / Waste per plan."""

    total_waste: float = 0.0
    """总余料 / Total waste."""

    precision: float = 1e-8
    """数值精度 / Numerical precision."""

    @staticmethod
    def create(
        *,
        material_lengths: tuple[float, ...],
    ) -> WasteModel:
        """创建余料模型。

        Create waste model.

        Args:
            material_lengths: 可用材料长度。
                Available material lengths.

        Returns:
            余料模型实例。
            Waste model instance.
        """
        return WasteModel(material_lengths=material_lengths)

    def with_waste_data(
        self,
        *,
        waste_data: tuple[tuple[str, float], ...],
    ) -> WasteModel:
        """创建包含余料数据的新模型。

        Create new model with waste data.

        Args:
            waste_data: 切割方案键到余料量的映射。
                Plan key to waste amount mapping.

        Returns:
            新模型实例。
            New model instance.
        """
        total = sum(w for _, w in waste_data)
        return WasteModel(
            material_lengths=self.material_lengths,
            waste_per_plan=waste_data,
            total_waste=total,
            precision=self.precision,
        )

    def get_waste_for_plan(self, plan_key: str) -> float:
        """获取指定切割方案的余料。

        Get waste for the specified cutting plan.

        Args:
            plan_key: 切割方案键。
                Cutting plan key.

        Returns:
            余料量，不存在返回 0.0。
            Waste amount, 0.0 if not found.
        """
        for key, waste in self.waste_per_plan:
            if key == plan_key:
                return waste
        return 0.0

    @property
    def average_waste(self) -> float:
        """获取平均余料。

        Get average waste.

        Returns:
            平均余料量。
            Average waste amount.
        """
        if not self.waste_per_plan:
            return 0.0
        return self.total_waste / len(self.waste_per_plan)

    @property
    def plan_count(self) -> int:
        """获取切割方案数量。

        Get number of cutting plans.

        Returns:
            方案数量。
            Number of plans.
        """
        return len(self.waste_per_plan)
