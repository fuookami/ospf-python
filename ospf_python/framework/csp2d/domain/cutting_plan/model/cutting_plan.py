"""切割方案模型 / Cutting plan model.

CSP2D 中的二维切割方案定义。
2D cutting plan definition in CSP2D.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.framework.csp2d.domain.material.model.sheet import (
    Sheet,
)
from ospf_python.framework.csp2d.domain.material.model.strip import (
    Strip,
)


@dataclass(frozen=True)
class CuttingItem:
    """切割项 / Cutting item.

    描述切割方案中的单个产品放置。
    Describes a single product placement in a cutting plan.

    Attributes:
        shape_key: 形状键 / Shape key.
        x: 放置 X 坐标 / Placement X coordinate.
        y: 放置 Y 坐标 / Placement Y coordinate.
        rotated: 是否旋转放置 / Whether placed rotated.
    """

    shape_key: str
    """形状键 / Shape key."""

    x: float
    """X 坐标 / X coordinate."""

    y: float
    """Y 坐标 / Y coordinate."""

    rotated: bool
    """是否旋转 / Whether rotated."""

    @staticmethod
    def create(
        *,
        shape_key: str,
        x: float,
        y: float,
        rotated: bool = False,
    ) -> CuttingItem:
        """创建切割项 / Create cutting item.

        Args:
            shape_key: 形状键 / Shape key.
            x: X 坐标 / X coordinate.
            y: Y 坐标 / Y coordinate.
            rotated: 是否旋转，默认 False /
                Whether rotated, default False.

        Returns:
            切割项实例 / CuttingItem instance.
        """
        return CuttingItem(
            shape_key=shape_key,
            x=x,
            y=y,
            rotated=rotated,
        )


MaterialType = Sheet | Strip


@dataclass(frozen=True)
class CuttingPlan:
    """切割方案 / Cutting plan.

    描述从一块材料上切割产品的完整方案，
    包括放置位置和浪费率。
    Describes a complete plan for cutting products from a material,
    including placement positions and waste ratio.

    Attributes:
        plan_key: 方案唯一键 / Plan unique key.
        material_key: 材料键 / Material key.
        items: 切割项元组 / Tuple of cutting items.
        waste_ratio: 浪费率（0.0~1.0） / Waste ratio (0.0~1.0).
    """

    plan_key: str
    """方案唯一键 / Plan unique key."""

    material_key: str
    """材料键 / Material key."""

    items: tuple[CuttingItem, ...]
    """切割项元组 / Tuple of cutting items."""

    waste_ratio: float
    """浪费率 / Waste ratio."""

    @staticmethod
    def create(
        *,
        plan_key: str,
        material_key: str,
        items: tuple[CuttingItem, ...] = (),
        waste_ratio: float = 0.0,
    ) -> CuttingPlan:
        """创建切割方案 / Create cutting plan.

        Args:
            plan_key: 方案唯一键 / Plan unique key.
            material_key: 材料键 / Material key.
            items: 切割项元组，默认空 /
                Cutting items, default empty.
            waste_ratio: 浪费率，默认 0.0 /
                Waste ratio, default 0.0.

        Returns:
            切割方案实例 / CuttingPlan instance.
        """
        return CuttingPlan(
            plan_key=plan_key,
            material_key=material_key,
            items=items,
            waste_ratio=waste_ratio,
        )

    @property
    def item_count(self) -> int:
        """切割项数量 / Cutting item count.

        Returns:
            切割项元组长度 / Length of items tuple.
        """
        return len(self.items)

    @property
    def total_item_area(self) -> float:
        """切割项总面积 / Total item area.

        注：此属性不包含形状尺寸信息，仅返回项数占位。
        实际面积计算需结合形状定义。
        Note: This property does not carry shape dimensions,
        so it returns a alternative. Actual area calculation
        requires shape definitions.

        Returns:
            切割项数量（占位） / Item count (alternative).
        """
        return float(self.item_count)

    @property
    def used_area(self) -> float:
        """已使用面积占比 / Used area ratio.

        Returns:
            1.0 减去浪费率 / 1.0 minus waste ratio.
        """
        return 1.0 - self.waste_ratio

    def is_valid_for(
        self,
        material: MaterialType,
    ) -> bool:
        """检查方案是否对指定材料有效 /
        Check if plan is valid for material.

        验证浪费率在合理范围内，且材料键匹配。
        Validates waste ratio is in a reasonable range and
        material key matches.

        Args:
            material: 目标材料 / Target material.

        Returns:
            是否有效 / Whether valid.
        """
        if self.waste_ratio < 0.0 or self.waste_ratio > 1.0:
            return False
        if self.material_key != material.name:
            return False
        if self.item_count == 0:
            return self.waste_ratio == 1.0
        return 0.0 <= self.waste_ratio <= 1.0

    def add_item(
        self,
        item: CuttingItem,
    ) -> CuttingPlan:
        """添加切割项 / Add cutting item.

        返回包含新项的新方案实例（不可变模式）。
        Returns a new plan instance with the added item
        (immutable pattern).

        Args:
            item: 要添加的切割项 / Cutting item to add.

        Returns:
            新切割方案实例 / New CuttingPlan instance.
        """
        return CuttingPlan(
            plan_key=self.plan_key,
            material_key=self.material_key,
            items=(*self.items, item),
            waste_ratio=self.waste_ratio,
        )

    def waste_area(
        self,
        material: MaterialType,
    ) -> float:
        """计算浪费面积 / Calculate waste area.

        Args:
            material: 目标材料 / Target material.

        Returns:
            浪费面积 / Waste area.
        """
        return material.area * self.waste_ratio
