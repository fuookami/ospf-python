"""重量分布目标 / Weight distribution objective.

最小化装载方案的重量不平衡度。
Minimizes the weight imbalance of a stowage plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.stowage_item import (
        StowageItem,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_position import (
        StowagePosition,
    )


@dataclass(frozen=True)
class ImbalanceTerm:
    """不平衡项 / Imbalance term.

    表示目标函数中一个不平衡度的加权项。
    Represents a weighted term of imbalance in the
    objective function.

    Attributes:
        axis: 轴（LATERAL/LONGITUDINAL）/
            Axis (LATERAL/LONGITUDINAL).
        weight_coefficient: 权重系数 / Weight coefficient.
        moment: 力矩值 / Moment value.
        variable_name: 关联变量名 / Associated variable name.
    """

    axis: str = ""
    """轴 / Axis."""

    weight_coefficient: float = 0.0
    """权重系数 / Weight coefficient."""

    moment: float = 0.0
    """力矩值 / Moment value."""

    variable_name: str = ""
    """关联变量名 / Associated variable name."""


@dataclass(frozen=True)
class WeightDistributionObjective:
    """重量分布目标 / Weight distribution objective.

    构建最小化重量不平衡度的目标函数项。通过同时最小化
    横向和纵向力矩的绝对值，鼓励货物均匀分布。
    Builds objective function terms for minimizing weight
    imbalance. By minimizing the absolute values of both
    lateral and longitudinal moments, encourages uniform
    cargo distribution.

    Attributes:
        objective_name: 目标函数名称 / Objective function name.
        lateral_weight: 横向权重 / Lateral weight.
        longitudinal_weight: 纵向权重 / Longitudinal weight.
    """

    objective_name: str = "weight_distribution"
    """目标函数名称 / Objective function name."""

    lateral_weight: float = 1.0
    """横向权重 / Lateral weight."""

    longitudinal_weight: float = 1.0
    """纵向权重 / Longitudinal weight."""

    @staticmethod
    def create(
        *,
        lateral_weight: float = 1.0,
        longitudinal_weight: float = 1.0,
    ) -> WeightDistributionObjective:
        """创建重量分布目标。

        Create weight distribution objective.

        Args:
            lateral_weight: 横向权重。/ Lateral weight.
            longitudinal_weight: 纵向权重。/ Longitudinal weight.

        Returns:
            目标实例。/ Objective instance.
        """
        return WeightDistributionObjective(
            lateral_weight=lateral_weight,
            longitudinal_weight=longitudinal_weight,
        )

    def build_objective_terms(
        self,
        item_placements: tuple[tuple[StowageItem, StowagePosition], ...],
    ) -> tuple[ImbalanceTerm, ...]:
        """构建目标函数项。

        Build objective function terms.

        Args:
            item_placements: 货物及其位置的配对列表。/
                List of item-position pairs.

        Returns:
            不平衡项元组。/ Tuple of imbalance terms.
        """
        lateral_moment = 0.0
        longitudinal_moment = 0.0
        for item, pos in item_placements:
            lateral_moment += pos.lateral_moment(item.weight)
            longitudinal_moment += pos.longitudinal_moment(
                item.weight,
            )
        terms: list[ImbalanceTerm] = []
        if self.lateral_weight > 0.0:
            terms.append(
                ImbalanceTerm(
                    axis="LATERAL",
                    weight_coefficient=self.lateral_weight,
                    moment=lateral_moment,
                    variable_name="lateral_imbalance",
                )
            )
        if self.longitudinal_weight > 0.0:
            terms.append(
                ImbalanceTerm(
                    axis="LONGITUDINAL",
                    weight_coefficient=self.longitudinal_weight,
                    moment=longitudinal_moment,
                    variable_name="longitudinal_imbalance",
                )
            )
        return tuple(terms)

    def calculate_imbalance(
        self,
        item_placements: tuple[tuple[StowageItem, StowagePosition], ...],
    ) -> float:
        """计算总不平衡度。

        Calculate total imbalance.

        Args:
            item_placements: 货物及其位置的配对列表。/
                List of item-position pairs.

        Returns:
            加权不平衡度值。/ Weighted imbalance value.
        """
        terms = self.build_objective_terms(item_placements)
        return sum(t.weight_coefficient * abs(t.moment) for t in terms)

    def objective_name_for(self, axis: str) -> str:
        """生成轴特定的目标函数名称。

        Generate axis-specific objective function name.

        Args:
            axis: 轴名称。/ Axis name.

        Returns:
            目标函数名称。/ Objective function name.
        """
        return f"{self.objective_name}_{axis.lower()}"
