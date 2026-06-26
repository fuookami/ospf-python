"""重心约束。

Center of gravity constraint for vehicle/aircraft stability.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CGItem:
    """重心物品信息。

    Item with position and weight for CG calculation.

    Attributes:
        item_id: 物品标识 / Item identifier
        weight: 物品重量（千克）/ Item weight (kg)
        position: 物品位置 (x, y, z) / Item position coordinates
    """

    item_id: str
    weight: float
    position: tuple[float, float, float]


@dataclass(frozen=True)
class CenterOfGravityLimit:
    """重心限制范围。

    Defines acceptable CG envelope.

    Attributes:
        x_range: X轴范围 (最小, 最大) / X-axis range (min, max)
        y_range: Y轴范围 (最小, 最大) / Y-axis range (min, max)
        z_range: Z轴范围 (最小, 最大) / Z-axis range (min, max)
    """

    x_range: tuple[float, float]
    y_range: tuple[float, float]
    z_range: tuple[float, float]


@dataclass(frozen=True)
class CenterOfGravityConstraint:
    """重心位置约束。

    Enforces that the overall center of gravity of loaded cargo stays
    within the acceptable envelope for vehicle or aircraft stability.

    Attributes:
        cg_limit: 重心可接受范围 / Acceptable CG envelope
    """

    cg_limit: CenterOfGravityLimit

    def evaluate(
        self,
        items: tuple[CGItem, ...],
    ) -> tuple[bool, tuple[float, float, float]]:
        """评估重心约束。

        Computes the loaded CG and checks against the acceptable envelope.

        Args:
            items: 所有装载物品 / All loaded items

        Returns:
            tuple: (是否满足, 重心坐标) / (satisfied, CG coordinates)
        """
        cg = self.compute_cg(items)
        within_x = self.cg_limit.x_range[0] <= cg[0] <= self.cg_limit.x_range[1]
        within_y = self.cg_limit.y_range[0] <= cg[1] <= self.cg_limit.y_range[1]
        within_z = self.cg_limit.z_range[0] <= cg[2] <= self.cg_limit.z_range[1]
        return (within_x and within_y and within_z, cg)

    @staticmethod
    def compute_cg(
        items: tuple[CGItem, ...],
    ) -> tuple[float, float, float]:
        """计算加权重心坐标。

        Computes the weight-averaged center of gravity.

        Args:
            items: 所有物品 / All items

        Returns:
            tuple: (cx, cy, cz) 重心坐标 / CG coordinates
        """
        total_weight = sum(item.weight for item in items)
        if total_weight == 0.0:
            return (0.0, 0.0, 0.0)
        cx = sum(item.weight * item.position[0] for item in items) / total_weight
        cy = sum(item.weight * item.position[1] for item in items) / total_weight
        cz = sum(item.weight * item.position[2] for item in items) / total_weight
        return (cx, cy, cz)

    def cg_margin(
        self,
        cg: tuple[float, float, float],
    ) -> tuple[float, float, float]:
        """计算重心到限制边界的余量。

        Computes the margin between the CG and each limit boundary.
        Positive values mean the CG is within bounds.

        Args:
            cg: 重心坐标 / CG coordinates

        Returns:
            tuple: (x余量, y余量, z余量) / (x, y, z margins)
        """
        x_margin = min(
            cg[0] - self.cg_limit.x_range[0],
            self.cg_limit.x_range[1] - cg[0],
        )
        y_margin = min(
            cg[1] - self.cg_limit.y_range[0],
            self.cg_limit.y_range[1] - cg[1],
        )
        z_margin = min(
            cg[2] - self.cg_limit.z_range[0],
            self.cg_limit.z_range[1] - cg[2],
        )
        return (x_margin, y_margin, z_margin)
