"""燃油效率目标 / Fuel efficiency objective.

通过优化重量分布来提高燃油效率。
Improves fuel efficiency by optimizing weight placement.
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
class FuelEfficiencyTerm:
    """燃油效率项 / Fuel efficiency term.

    表示目标函数中一个货物位置的燃油影响加权项。
    Represents a weighted fuel impact term for an item
    position in the objective function.

    Attributes:
        item_id: 货物标识 / Item identifier.
        fuel_impact: 燃油影响值 / Fuel impact value.
        weight_coefficient: 权重系数 / Weight coefficient.
        variable_name: 关联变量名 / Associated variable name.
    """

    item_id: str = ""
    """货物标识 / Item identifier."""

    fuel_impact: float = 0.0
    """燃油影响值 / Fuel impact value."""

    weight_coefficient: float = 0.0
    """权重系数 / Weight coefficient."""

    variable_name: str = ""
    """关联变量名 / Associated variable name."""


@dataclass(frozen=True)
class FuelEfficiencyObjective:
    """燃油效率目标 / Fuel efficiency objective.

    构建优化燃油效率的目标函数项。通过将重物放置在靠近
    飞机重心的位置来减少配平阻力，从而降低燃油消耗。
    Builds objective function terms for optimizing fuel efficiency.
    By placing heavy items near the aircraft CG, reduces trim
    drag and thus fuel consumption.

    Attributes:
        objective_name: 目标函数名称 / Objective function name.
        cg_x: 理想重心纵向坐标 /
            Ideal CG longitudinal coordinate.
        cg_y: 理想重心横向坐标 /
            Ideal CG lateral coordinate.
        longitudinal_weight: 纵向权重 /
            Longitudinal weight.
        lateral_weight: 横向权重 /
            Lateral weight.
    """

    objective_name: str = "fuel_efficiency"
    """目标函数名称 / Objective function name."""

    cg_x: float = 0.0
    """理想重心纵向坐标 / Ideal CG longitudinal coordinate."""

    cg_y: float = 0.0
    """理想重心横向坐标 / Ideal CG lateral coordinate."""

    longitudinal_weight: float = 2.0
    """纵向权重 / Longitudinal weight."""

    lateral_weight: float = 1.0
    """横向权重 / Lateral weight."""

    @staticmethod
    def create(
        *,
        cg_x: float = 0.0,
        cg_y: float = 0.0,
        longitudinal_weight: float = 2.0,
        lateral_weight: float = 1.0,
    ) -> FuelEfficiencyObjective:
        """创建燃油效率目标。

        Create fuel efficiency objective.

        Args:
            cg_x: 理想重心纵向坐标。/ Ideal CG x coordinate.
            cg_y: 理想重心横向坐标。/ Ideal CG y coordinate.
            longitudinal_weight: 纵向权重。/ Longitudinal weight.
            lateral_weight: 横向权重。/ Lateral weight.

        Returns:
            目标实例。/ Objective instance.
        """
        return FuelEfficiencyObjective(
            cg_x=cg_x,
            cg_y=cg_y,
            longitudinal_weight=longitudinal_weight,
            lateral_weight=lateral_weight,
        )

    def build_objective_terms(
        self,
        item_placements: tuple[tuple[StowageItem, StowagePosition], ...],
    ) -> tuple[FuelEfficiencyTerm, ...]:
        """构建目标函数项。

        Build objective function terms.

        Args:
            item_placements: 货物及其位置的配对列表。/
                List of item-position pairs.

        Returns:
            燃油效率项元组。/ Tuple of fuel efficiency terms.
        """
        terms: list[FuelEfficiencyTerm] = []
        for item, pos in item_placements:
            impact = self._fuel_impact(item, pos)
            terms.append(
                FuelEfficiencyTerm(
                    item_id=item.item_id,
                    fuel_impact=impact,
                    weight_coefficient=1.0,
                    variable_name=self._var_name(
                        item.item_id,
                    ),
                )
            )
        return tuple(terms)

    def calculate_total_impact(
        self,
        item_placements: tuple[tuple[StowageItem, StowagePosition], ...],
    ) -> float:
        """计算总燃油影响。

        Calculate total fuel impact.

        Args:
            item_placements: 货物及其位置的配对列表。/
                List of item-position pairs.

        Returns:
            总燃油影响值。/ Total fuel impact value.
        """
        terms = self.build_objective_terms(item_placements)
        return sum(t.weight_coefficient * t.fuel_impact for t in terms)

    def _fuel_impact(
        self,
        item: StowageItem,
        position: StowagePosition,
    ) -> float:
        """计算单个货物的燃油影响。

        Calculate fuel impact for a single item.

        Args:
            item: 货物。/ Item.
            position: 位置。/ Position.

        Returns:
            燃油影响值。/ Fuel impact value.
        """
        dx = position.x - self.cg_x
        dy = position.y - self.cg_y
        longitudinal_penalty = abs(dx) * self.longitudinal_weight
        lateral_penalty = abs(dy) * self.lateral_weight
        return item.weight * (longitudinal_penalty + lateral_penalty)

    @staticmethod
    def _var_name(item_id: str) -> str:
        """生成变量名称。

        Generate variable name.

        Args:
            item_id: 货物标识。/ Item identifier.

        Returns:
            变量名称字符串。/ Variable name string.
        """
        return f"fuel_eff_{item_id}"
