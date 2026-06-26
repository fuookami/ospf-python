"""空间利用目标 / Space utilization objective.

最大化货舱的空间利用率。
Maximizes compartment space utilization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from examples.framework_demo.demo2.domain.stowage.model.stowage_density import (
    StowageDensity,
)

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.stowage_compartment import (
        StowageCompartment,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_item import (
        StowageItem,
    )


@dataclass(frozen=True)
class UtilizationTerm:
    """利用率项 / Utilization term.

    表示目标函数中一个货舱的利用率加权项。
    Represents a weighted utilization term for a compartment
    in the objective function.

    Attributes:
        compartment_id: 舱室标识 / Compartment identifier.
        weight_coefficient: 权重系数 / Weight coefficient.
        density: 装载密度 / Stowage density.
        variable_name: 关联变量名 / Associated variable name.
    """

    compartment_id: str = ""
    """舱室标识 / Compartment identifier."""

    weight_coefficient: float = 0.0
    """权重系数 / Weight coefficient."""

    density: StowageDensity = None  # type: ignore[assignment]
    """装载密度 / Stowage density."""

    variable_name: str = ""
    """关联变量名 / Associated variable name."""


@dataclass(frozen=True)
class SpaceUtilizationObjective:
    """空间利用目标 / Space utilization objective.

    构建最大化空间利用率的目标函数项。通过计算每个货舱的
    容积利用率并加权求和，鼓励充分利用可用空间。
    Builds objective function terms for maximizing space
    utilization. Computes volume utilization for each compartment
    and sums weighted values to encourage full use of available
    space.

    Attributes:
        objective_name: 目标函数名称 / Objective function name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "space_utilization"
    """目标函数名称 / Objective function name."""

    default_weight: float = 1.0
    """默认权重 / Default weight."""

    def build_objective_terms(
        self,
        *,
        compartments: tuple[StowageCompartment, ...],
        items: tuple[StowageItem, ...],
        assignments: dict[str, tuple[str, ...]],
        weights: dict[str, float] | None = None,
    ) -> tuple[UtilizationTerm, ...]:
        """构建目标函数项。

        Build objective function terms.

        Args:
            compartments: 货舱列表。/ Compartment list.
            items: 货物列表。/ Item list.
            assignments: 分配映射。/ Assignment mapping.
            weights: 自定义权重映射。/ Custom weight mapping.

        Returns:
            利用率项元组。/ Tuple of utilization terms.
        """
        effective_weights = weights or {}
        item_map = {item.item_id: item for item in items}
        terms: list[UtilizationTerm] = []
        for comp in compartments:
            assigned_ids = assignments.get(comp.comp_id, ())
            volume_used = sum(
                item_map[sid].volume for sid in assigned_ids if sid in item_map
            )
            density = StowageDensity.from_usage(
                compartment_id=comp.comp_id,
                volume_used=volume_used,
                max_volume=comp.max_volume,
            )
            weight = effective_weights.get(
                comp.comp_id,
                self.default_weight,
            )
            if weight > 0.0:
                terms.append(
                    UtilizationTerm(
                        compartment_id=comp.comp_id,
                        weight_coefficient=weight,
                        density=density,
                        variable_name=self._var_name(
                            comp.comp_id,
                        ),
                    )
                )
        return tuple(terms)

    def calculate_utilization(
        self,
        *,
        compartments: tuple[StowageCompartment, ...],
        items: tuple[StowageItem, ...],
        assignments: dict[str, tuple[str, ...]],
    ) -> float:
        """计算总空间利用率。

        Calculate total space utilization.

        Args:
            compartments: 货舱列表。/ Compartment list.
            items: 货物列表。/ Item list.
            assignments: 分配映射。/ Assignment mapping.

        Returns:
            加权利用率值。/ Weighted utilization value.
        """
        terms = self.build_objective_terms(
            compartments=compartments,
            items=items,
            assignments=assignments,
        )
        return sum(t.weight_coefficient * t.density.density_ratio for t in terms)

    def average_utilization(
        self,
        *,
        compartments: tuple[StowageCompartment, ...],
        items: tuple[StowageItem, ...],
        assignments: dict[str, tuple[str, ...]],
    ) -> float:
        """计算平均空间利用率。

        Calculate average space utilization.

        Args:
            compartments: 货舱列表。/ Compartment list.
            items: 货物列表。/ Item list.
            assignments: 分配映射。/ Assignment mapping.

        Returns:
            平均利用率，无货舱时返回 0.0。
            Average utilization, or 0.0 if no compartments.
        """
        terms = self.build_objective_terms(
            compartments=compartments,
            items=items,
            assignments=assignments,
        )
        if not terms:
            return 0.0
        total = sum(t.density.density_ratio for t in terms)
        return total / len(terms)

    def _var_name(self, compartment_id: str) -> str:
        """生成变量名称。

        Generate variable name.

        Args:
            compartment_id: 舱室标识。/ Compartment identifier.

        Returns:
            变量名称字符串。/ Variable name string.
        """
        return f"utilization_{compartment_id}"
