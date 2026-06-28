"""切割方案生成器 / Cutting plan generator service.

CSP2D 切割方案生成服务，实现简单的左下放置启发式。
CSP2D cutting plan generation service, implementing a simple
left-bottom placement heuristic for rectangle packing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.framework.csp2d.domain.cutting_plan.model.cutting_plan import (
    CuttingItem,
    CuttingPlan,
)

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


@dataclass(frozen=True)
class _Placement:
    """内部放置记录 / Internal placement record.

    Attributes:
        shape_key: 形状键 / Shape key.
        x: X 坐标 / X coordinate.
        y: Y 坐标 / Y coordinate.
        w: 放置宽度 / Placed width.
        h: 放置高度 / Placed height.
        rotated: 是否旋转 / Whether rotated.
    """

    shape_key: str
    x: float
    y: float
    w: float
    h: float
    rotated: bool


class CuttingPlanGenerator:
    """切割方案生成器 / Cutting plan generator.

    实现简单的左下角放置（Bottom-Left）启发式算法，
    用于从二维板材上切割矩形产品。
    Implements a simple Bottom-Left (BL) heuristic algorithm
    for cutting rectangular products from 2D sheet materials.

    算法流程：
    1. 按面积降序排列待放置形状
    2. 尝试每个可行旋转方向
    3. 在所有可行位置中选择最左下角位置
    4. 重复直到无法继续放置
    Algorithm flow:
    1. Sort shapes by area descending
    2. Try each feasible rotation
    3. Pick the bottommost-leftmost feasible position
    4. Repeat until no more shapes can be placed
    """

    def generate_guillotine(
        self,
        material: Sheet,
        shapes: tuple[Shape, ...],
        demands: tuple[Demand, ...],
    ) -> tuple[CuttingPlan, ...]:
        """生成切割方案（启发式） / Generate cutting plans (heuristic).

        使用左下角放置策略为每块材料生成切割方案。
        Generates cutting plans for each material using
        the bottom-left placement strategy.

        Args:
            material: 目标板材 / Target sheet.
            shapes: 可用形状元组 / Available shapes tuple.
            demands: 需求元组 / Demands tuple.

        Returns:
            切割方案元组 / Tuple of cutting plans.
        """
        if not shapes or not demands:
            return tuple()  # reason: no shapes or demands to generate

        shape_map = {s.shape_key: s for s in shapes}
        remaining = self._build_remaining(demands)

        all_plans: list[CuttingPlan] = []
        plan_idx = 0

        while any(qty > 0 for qty in remaining.values()):
            placements = self._pack_one_sheet(
                material,
                shape_map,
                remaining,
            )
            if not placements:
                break

            items = tuple(
                CuttingItem(
                    shape_key=p.shape_key,
                    x=p.x,
                    y=p.y,
                    rotated=p.rotated,
                )
                for p in placements
            )

            used_area = sum(p.w * p.h for p in placements)
            waste_ratio = 1.0 - (
                used_area / material.area if material.area > 0 else 0.0
            )

            plan = CuttingPlan(
                plan_key=f"{material.name}_plan_{plan_idx}",
                material_key=material.name,
                items=items,
                waste_ratio=max(0.0, min(1.0, waste_ratio)),
            )
            all_plans.append(plan)
            plan_idx += 1

        return tuple(all_plans)

    def _build_remaining(
        self,
        demands: tuple[Demand, ...],
    ) -> dict[str, int]:
        """构建剩余需求映射 / Build remaining demand mapping.

        Args:
            demands: 需求元组 / Demands tuple.

        Returns:
            形状键到剩余数量的映射。
            Mapping from shape key to remaining quantity.
        """
        result: dict[str, int] = {}
        for d in demands:
            result[d.shape_key] = result.get(d.shape_key, 0) + d.quantity
        return result

    def _pack_one_sheet(
        self,
        material: Sheet,
        shape_map: dict[str, Shape],
        remaining: dict[str, int],
    ) -> tuple[_Placement, ...]:
        """在单块板材上放置产品 / Place products on a single sheet.

        使用左下角放置启发式。
        Uses the bottom-left placement heuristic.

        Args:
            material: 目标板材 / Target sheet.
            shape_map: 形状映射 / Shape mapping.
            remaining: 剩余需求 / Remaining demands.

        Returns:
            放置记录元组 / Placement record tuple.
        """
        placements: list[_Placement] = []
        occupied: list[tuple[float, float, float, float]] = []

        candidates = self._sorted_candidates(
            shape_map,
            remaining,
        )

        for shape_key, w, h, rotated in candidates:
            qty = remaining.get(shape_key, 0)
            if qty <= 0:
                continue

            placed_count = 0
            while remaining.get(shape_key, 0) > 0:
                pos = self._find_bl_position(
                    material.width,
                    material.height,
                    w,
                    h,
                    occupied,
                )
                if pos is None:
                    break

                px, py = pos
                placement = _Placement(
                    shape_key=shape_key,
                    x=px,
                    y=py,
                    w=w,
                    h=h,
                    rotated=rotated,
                )
                placements.append(placement)
                occupied.append((px, py, px + w, py + h))
                remaining[shape_key] = remaining.get(shape_key, 0) - 1
                placed_count += 1

        return tuple(placements)

    def _sorted_candidates(
        self,
        shape_map: dict[str, Shape],
        remaining: dict[str, int],
    ) -> list[tuple[str, float, float, bool]]:
        """排序放置候选 / Sort placement candidates.

        按面积降序排列，先尝试旋转方向。
        Sort by area descending, try rotation first.

        Args:
            shape_map: 形状映射 / Shape mapping.
            remaining: 剩余需求 / Remaining demands.

        Returns:
            (形状键, 宽, 高, 是否旋转) 列表。
            List of (shape_key, width, height, rotated).
        """
        candidates: list[tuple[str, float, float, bool]] = []
        for sk, qty in remaining.items():
            if qty <= 0:
                continue
            shape = shape_map.get(sk)
            if shape is None:
                continue
            for rotation in shape.rotations():
                candidates.append(
                    (sk, rotation.width, rotation.height, rotation is not shape),
                )

        candidates.sort(
            key=lambda c: c[1] * c[2],
            reverse=True,
        )
        return candidates

    def _find_bl_position(
        self,
        bin_w: float,
        bin_h: float,
        item_w: float,
        item_h: float,
        occupied: list[tuple[float, float, float, float]],
    ) -> tuple[float, float] | None:
        """查找最左下角可行位置 / Find bottom-left feasible position.

        扫描所有候选点，选择最左下角的不重叠位置。
        Scans all candidate points, picks the bottommost-leftmost
        non-overlapping position.

        Args:
            bin_w: 容器宽度 / Container width.
            bin_h: 容器高度 / Container height.
            item_w: 物品宽度 / Item width.
            item_h: 物品高度 / Item height.
            occupied: 已占用区域列表 / List of occupied regions.

        Returns:
            (x, y) 坐标或 None / (x, y) coordinates or None.
        """
        if item_w > bin_w or item_h > bin_h:
            return None  # reason: item exceeds container dimensions

        step = max(item_w, item_h) / 2.0
        step = max(step, 1.0)

        y = 0.0
        while y + item_h <= bin_h + 1e-9:
            x = 0.0
            while x + item_w <= bin_w + 1e-9:
                if not self._overlaps(
                    x,
                    y,
                    item_w,
                    item_h,
                    occupied,
                ):
                    return (x, y)
                x += step
            y += step

        # 精细扫描 / Fine-grained scan
        y = 0.0
        while y + item_h <= bin_h + 1e-9:
            x = 0.0
            while x + item_w <= bin_w + 1e-9:
                if not self._overlaps(
                    x,
                    y,
                    item_w,
                    item_h,
                    occupied,
                ):
                    return (x, y)
                x += 1.0
            y += 1.0

        return None  # reason: no feasible position found after full scan

    def _overlaps(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        occupied: list[tuple[float, float, float, float]],
    ) -> bool:
        """检查是否与已占用区域重叠 / Check overlap with occupied regions.

        Args:
            x: 放置 X 坐标 / Placement X.
            y: 放置 Y 坐标 / Placement Y.
            w: 放置宽度 / Placement width.
            h: 放置高度 / Placement height.
            occupied: 已占用区域 / Occupied regions.

        Returns:
            是否重叠 / Whether overlaps.
        """
        new_x2 = x + w
        new_y2 = y + h
        has_overlap = any(
            x < ox2 and new_x2 > ox1 and y < oy2 and new_y2 > oy1
            for ox1, oy1, ox2, oy2 in occupied
        )
        return has_overlap
