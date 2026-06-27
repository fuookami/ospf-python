"""材料优化器 / Material optimizer service.

CSP2D 材料选择优化服务，实现简单的贪心材料选择算法。
CSP2D material selection optimization service, implementing
a simple greedy material selection algorithm based on
waste minimization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.csp2d.domain.material.model.sheet import (
        Sheet,
    )
    from ospf_python.framework.csp2d.domain.product.model.demand import (
        Demand,
    )
    from ospf_python.framework.csp2d.domain.product.model.shape import (
        Shape,
    )


MaterialType = "Sheet | Strip"


@dataclass(frozen=True)
class MaterialSelection:
    """材料选择结果 / Material selection result.

    描述优化后的材料选择方案。
    Describes the optimized material selection plan.

    Attributes:
        material_name: 所选材料名称 / Selected material name.
        plan_count: 所需方案数 / Number of plans needed.
        total_waste_ratio: 总浪费率 / Total waste ratio.
        total_cost: 总成本 / Total cost.
    """

    material_name: str
    """材料名称 / Material name."""

    plan_count: int
    """方案数 / Plan count."""

    total_waste_ratio: float
    """总浪费率 / Total waste ratio."""

    total_cost: float
    """总成本 / Total cost."""


class MaterialOptimizer:
    """材料优化器 / Material optimizer.

    实现简单的贪心材料选择算法，基于浪费率最小化原则。
    Implements a simple greedy material selection algorithm
    based on waste minimization.

    算法流程：
    1. 计算所有需求的总面积
    2. 对每种候选材料估算所需数量和浪费率
    3. 按单位有效成本排序（成本 / (1 - 浪费率)）
    4. 选择单位有效成本最低的材料
    Algorithm flow:
    1. Calculate total area of all demands
    2. Estimate required quantity and waste ratio for each material
    3. Sort by effective unit cost (cost / (1 - waste ratio))
    4. Select material with lowest effective unit cost
    """

    def optimize(
        self,
        demands: tuple[Demand, ...],
        shapes: tuple[Shape, ...],
        materials: tuple[Sheet, ...],
    ) -> MaterialSelection | None:
        """优化材料选择 / Optimize material selection.

        从候选材料中选择浪费率最低的材料。
        Selects the material with lowest waste ratio
        from candidates.

        Args:
            demands: 需求元组 / Demands tuple.
            shapes: 形状元组 / Shapes tuple.
            materials: 候选板材元组 / Candidate sheets tuple.

        Returns:
            最优材料选择结果或 None（无可行材料时）。
            Best material selection or None (when no feasible material).
        """
        if not demands or not shapes or not materials:
            return None

        shape_map = {s.shape_key: s for s in shapes}
        total_area = self._calc_total_demand_area(
            demands,
            shape_map,
        )
        if total_area <= 0.0:
            return None

        best: MaterialSelection | None = None
        best_eff_cost = float("inf")

        for mat in materials:
            if mat.area <= 0.0:
                continue

            selection = self._evaluate_material(
                mat,
                total_area,
                demands,
                shape_map,
            )
            if selection is None:
                continue

            if selection.total_waste_ratio >= 1.0:
                continue

            eff_cost = selection.total_cost / (1.0 - selection.total_waste_ratio)
            if eff_cost < best_eff_cost:
                best_eff_cost = eff_cost
                best = selection

        return best

    def _calc_total_demand_area(
        self,
        demands: tuple[Demand, ...],
        shape_map: dict[str, Shape],
    ) -> float:
        """计算需求总面积 / Calculate total demand area.

        Args:
            demands: 需求元组 / Demands tuple.
            shape_map: 形状映射 / Shape mapping.

        Returns:
            总面积 / Total area.
        """
        total = 0.0
        for d in demands:
            shape = shape_map.get(d.shape_key)
            if shape is not None:
                total += shape.area * d.quantity
        return total

    def _evaluate_material(
        self,
        material: Sheet,
        total_area: float,
        demands: tuple[Demand, ...],
        shape_map: dict[str, Shape],
    ) -> MaterialSelection | None:
        """评估单种材料 / Evaluate a single material.

        估算所需材料数量和浪费率。
        Estimates required material count and waste ratio.

        Args:
            material: 候选材料 / Candidate material.
            total_area: 需求总面积 / Total demand area.
            demands: 需求元组 / Demands tuple.
            shape_map: 形状映射 / Shape mapping.

        Returns:
            材料选择结果或 None / Material selection or None.
        """
        if not self._can_fit_any(material, shape_map):
            return None

        raw_count = total_area / material.area
        import math

        plan_count = max(1, math.ceil(raw_count))

        used_area = total_area
        total_material_area = material.area * plan_count
        waste_ratio = 1.0 - (
            used_area / total_material_area if total_material_area > 0 else 0.0
        )

        total_cost = material.cost * plan_count

        return MaterialSelection(
            material_name=material.name,
            plan_count=plan_count,
            total_waste_ratio=max(0.0, waste_ratio),
            total_cost=total_cost,
        )

    def _can_fit_any(
        self,
        material: Sheet,
        shape_map: dict[str, Shape],
    ) -> bool:
        """检查是否有形状能放入材料 / Check if any shape fits in material.

        Args:
            material: 目标材料 / Target material.
            shape_map: 形状映射 / Shape mapping.

        Returns:
            是否有形状能放入 / Whether any shape fits.
        """
        for shape in shape_map.values():
            if shape.fits_in(material.width, material.height):
                return True
        return False

    def rank_materials(
        self,
        demands: tuple[Demand, ...],
        shapes: tuple[Shape, ...],
        materials: tuple[Sheet, ...],
    ) -> tuple[MaterialSelection, ...]:
        """对所有可行材料排名 / Rank all feasible materials.

        按总成本升序排列所有可行材料选择。
        Sorts all feasible material selections by total cost.

        Args:
            demands: 需求元组 / Demands tuple.
            shapes: 形状元组 / Shapes tuple.
            materials: 候选板材元组 / Candidate sheets tuple.

        Returns:
            排序后的材料选择结果元组。
            Sorted material selection tuple.
        """
        if not demands or not shapes or not materials:
            return ()

        shape_map = {s.shape_key: s for s in shapes}
        total_area = self._calc_total_demand_area(
            demands,
            shape_map,
        )
        if total_area <= 0.0:
            return ()

        selections: list[MaterialSelection] = []
        for mat in materials:
            if mat.area <= 0.0:
                continue
            sel = self._evaluate_material(
                mat,
                total_area,
                demands,
                shape_map,
            )
            if sel is not None and sel.total_waste_ratio < 1.0:
                selections.append(sel)

        selections.sort(key=lambda s: s.total_cost)
        return tuple(selections)
