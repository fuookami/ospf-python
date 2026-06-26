"""装载时间目标 / Loading time objective.

最小化货物装载所需时间。
Minimizes the time required for cargo loading.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.stowage_compartment import (
        StowageCompartment,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_item import (
        StowageItem,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_position import (
        StowagePosition,
    )


@dataclass(frozen=True)
class LoadingTimeTerm:
    """装载时间项 / Loading time term.

    表示目标函数中一个货物的装载时间加权项。
    Represents a weighted loading time term for an item
    in the objective function.

    Attributes:
        item_id: 货物标识 / Item identifier.
        estimated_time: 预估装载时间（秒）/
            Estimated loading time (seconds).
        weight_coefficient: 权重系数 / Weight coefficient.
        variable_name: 关联变量名 / Associated variable name.
    """

    item_id: str = ""
    """货物标识 / Item identifier."""

    estimated_time: float = 0.0
    """预估装载时间（秒）/ Estimated loading time (seconds)."""

    weight_coefficient: float = 0.0
    """权重系数 / Weight coefficient."""

    variable_name: str = ""
    """关联变量名 / Associated variable name."""


@dataclass(frozen=True)
class LoadingTimeObjective:
    """装载时间目标 / Loading time objective.

    构建最小化装载时间的目标函数项。预估每个货物的装载
    时间，考虑货物重量、距离和货舱深度等因素。
    Builds objective function terms for minimizing loading time.
    Estimates loading time for each item, considering weight,
    distance, and compartment depth factors.

    Attributes:
        objective_name: 目标函数名称 / Objective function name.
        base_time_per_kg: 每千克基础时间（秒）/
            Base time per kg (seconds).
        distance_factor: 距离因子 /
            Distance factor.
    """

    objective_name: str = "loading_time"
    """目标函数名称 / Objective function name."""

    base_time_per_kg: float = 0.1
    """每千克基础时间（秒）/ Base time per kg (seconds)."""

    distance_factor: float = 0.5
    """距离因子 / Distance factor."""

    def build_objective_terms(
        self,
        *,
        items: tuple[StowageItem, ...],
        positions: dict[str, StowagePosition],
        compartments: tuple[StowageCompartment, ...],
        weights: dict[str, float] | None = None,
    ) -> tuple[LoadingTimeTerm, ...]:
        """构建目标函数项。

        Build objective function terms.

        Args:
            items: 货物列表。/ Item list.
            positions: 货物位置映射。/ Item position mapping.
            compartments: 货舱列表。/ Compartment list.
            weights: 自定义权重。/ Custom weights.

        Returns:
            装载时间项元组。/ Tuple of loading time terms.
        """
        effective_weights = weights or {}
        comp_map = {c.comp_id: c for c in compartments}
        terms: list[LoadingTimeTerm] = []
        for item in items:
            pos = positions.get(item.item_id)
            if pos is None:
                continue
            comp = comp_map.get(pos.compartment)
            time_est = self._estimate_time(
                item=item,
                position=pos,
                compartment_depth=(
                    comp.max_volume ** (1.0 / 3.0) if comp is not None else 10.0
                ),
            )
            weight = effective_weights.get(
                item.item_id,
                1.0,
            )
            if weight > 0.0:
                terms.append(
                    LoadingTimeTerm(
                        item_id=item.item_id,
                        estimated_time=time_est,
                        weight_coefficient=weight,
                        variable_name=self._var_name(
                            item.item_id,
                        ),
                    )
                )
        return tuple(terms)

    def calculate_total_time(
        self,
        *,
        items: tuple[StowageItem, ...],
        positions: dict[str, StowagePosition],
        compartments: tuple[StowageCompartment, ...],
    ) -> float:
        """计算总装载时间。

        Calculate total loading time.

        Args:
            items: 货物列表。/ Item list.
            positions: 货物位置映射。/ Item position mapping.
            compartments: 货舱列表。/ Compartment list.

        Returns:
            总装载时间（秒）。/ Total loading time (seconds).
        """
        terms = self.build_objective_terms(
            items=items,
            positions=positions,
            compartments=compartments,
        )
        return sum(t.estimated_time for t in terms)

    def _estimate_time(
        self,
        *,
        item: StowageItem,
        position: StowagePosition,
        compartment_depth: float,
    ) -> float:
        """估算单个货物的装载时间。

        Estimate loading time for a single item.

        Args:
            item: 货物。/ Item.
            position: 位置。/ Position.
            compartment_depth: 货舱深度。/ Compartment depth.

        Returns:
            预估时间（秒）。/ Estimated time (seconds).
        """
        base = item.weight * self.base_time_per_kg
        distance = float((position.x**2 + position.y**2) ** 0.5)
        distance_time = distance * self.distance_factor
        depth_time = position.z * 0.2
        return base + distance_time + depth_time

    @staticmethod
    def _var_name(item_id: str) -> str:
        """生成变量名称。

        Generate variable name.

        Args:
            item_id: 货物标识。/ Item identifier.

        Returns:
            变量名称字符串。/ Variable name string.
        """
        return f"loading_time_{item_id}"
