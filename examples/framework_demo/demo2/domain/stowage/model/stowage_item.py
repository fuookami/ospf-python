"""装载货物定义 / Stowage item definition.

定义需要装载的单件货物。
Defines a single cargo item to be loaded.
"""

from __future__ import annotations

from dataclasses import dataclass

from examples.framework_demo.demo2.domain.stowage.model.stowage_priority import (
    StowagePriority,
)


@dataclass(frozen=True)
class Dimensions:
    """货物尺寸 / Cargo dimensions.

    描述货物的三维尺寸（米）。
    Describes three-dimensional cargo size (meters).

    Attributes:
        length: 长度 / Length.
        width: 宽度 / Width.
        height: 高度 / Height.
    """

    length: float = 0.0
    """长度（米）/ Length (m)."""

    width: float = 0.0
    """宽度（米）/ Width (m)."""

    height: float = 0.0
    """高度（米）/ Height (m)."""

    @property
    def volume(self) -> float:
        """体积（立方米）。

        Volume (cubic meters).

        Returns:
            长 x 宽 x 高。/ Length x Width x Height.
        """
        return self.length * self.width * self.height


@dataclass(frozen=True)
class StowageItem:
    """装载货物 / Stowage item.

    描述需要装载到飞机上的单件货物，包含重量、尺寸、
    易碎性和优先级信息。
    Describes a single cargo item to be loaded onto an aircraft,
    including weight, dimensions, fragility, and priority.

    Attributes:
        item_id: 货物标识 / Item identifier.
        weight: 货物重量（千克）/ Item weight (kg).
        dimensions: 货物尺寸 / Item dimensions.
        fragility: 易碎等级（0=坚固, 1=极碎）/
            Fragility level (0=sturdy, 1=extremely fragile).
        priority: 装载优先级 / Loading priority.
    """

    item_id: str = ""
    """货物标识 / Item identifier."""

    weight: float = 0.0
    """货物重量（千克）/ Item weight (kg)."""

    dimensions: Dimensions = Dimensions()
    """货物尺寸 / Item dimensions."""

    fragility: float = 0.0
    """易碎等级（0.0-1.0）/ Fragility level (0.0-1.0)."""

    priority: StowagePriority = StowagePriority.MEDIUM
    """装载优先级 / Loading priority."""

    @staticmethod
    def create(
        *,
        item_id: str,
        weight: float,
        dimensions: Dimensions,
        fragility: float = 0.0,
        priority: StowagePriority = StowagePriority.MEDIUM,
    ) -> StowageItem:
        """创建装载货物。

        Create stowage item.

        Args:
            item_id: 货物标识。/ Item identifier.
            weight: 重量（千克）。/ Weight (kg).
            dimensions: 尺寸。/ Dimensions.
            fragility: 易碎等级，默认 0.0。/
                Fragility level, default 0.0.
            priority: 优先级，默认 MEDIUM。/
                Priority, default MEDIUM.

        Returns:
            货物实例。/ Item instance.
        """
        return StowageItem(
            item_id=item_id,
            weight=weight,
            dimensions=dimensions,
            fragility=max(0.0, min(1.0, fragility)),
            priority=priority,
        )

    @property
    def volume(self) -> float:
        """货物体积（立方米）。

        Item volume (cubic meters).

        Returns:
            尺寸对应的体积。/ Volume from dimensions.
        """
        return self.dimensions.volume

    @property
    def is_fragile(self) -> bool:
        """是否为易碎品。

        Whether the item is fragile.

        Returns:
            易碎等级大于 0.5 时返回 True。
            True if fragility level exceeds 0.5.
        """
        return self.fragility > 0.5

    @property
    def density(self) -> float:
        """货物密度（千克/立方米）。

        Item density (kg/cubic meter).

        Returns:
            重量除以体积，体积为零时返回 0.0。
            Weight divided by volume, or 0.0 if volume is zero.
        """
        vol = self.volume
        if vol <= 0.0:
            return 0.0
        return self.weight / vol

    def stacking_resistance(self) -> float:
        """计算堆叠抗压能力。

        Calculate stacking resistance.

        Returns:
            0.0（最弱）到 1.0（最强）的抗压值。
            Resistance value from 0.0 (weakest) to 1.0 (strongest).
        """
        return max(0.0, 1.0 - self.fragility)
