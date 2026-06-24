"""CSP1D 切割方案产品排序。

描述切割方案中产品的排列顺序。
Product order within a cutting plan.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CuttingPlanProductOrder:
    """切割方案产品排序 / Cutting plan product order.

    描述切割方案中各产品的排列顺序和数量，
    用于确定切割时的实际切法。
    Describes the order and quantity of products
    in a cutting plan, used to determine the
    actual cutting method.

    Attributes:
        product_key: 产品标识 / Product identifier.
        order_index: 排列序号 / Order index.
        quantity: 切割数量 / Cut quantity.
        width: 产品宽度 / Product width.
        length: 产品长度 / Product length.
    """

    product_key: str = ""
    """产品标识 / Product identifier."""

    order_index: int = 0
    """排列序号 / Order index."""

    quantity: int = 0
    """切割数量 / Cut quantity."""

    width: float = 0.0
    """产品宽度 / Product width."""

    length: float = 0.0
    """产品长度 / Product length."""

    @staticmethod
    def create(
        *,
        product_key: str,
        order_index: int,
        quantity: int,
        width: float = 0.0,
        length: float = 0.0,
    ) -> CuttingPlanProductOrder:
        """创建产品排序实例。

        Create product order instance.

        Args:
            product_key: 产品标识。
                Product identifier.
            order_index: 排列序号。
                Order index.
            quantity: 切割数量。
                Cut quantity.
            width: 产品宽度，默认 0.0。
                Product width, default 0.0.
            length: 产品长度，默认 0.0。
                Product length, default 0.0.

        Returns:
            产品排序实例。
            Product order instance.
        """
        return CuttingPlanProductOrder(
            product_key=product_key,
            order_index=order_index,
            quantity=quantity,
            width=width,
            length=length,
        )

    @property
    def total_width(self) -> float:
        """获取总宽度。

        Get total width.

        Returns:
            宽度乘数量。
            Width times quantity.
        """
        return self.width * self.quantity

    @property
    def total_length(self) -> float:
        """获取总长度。

        Get total length.

        Returns:
            长度乘数量。
            Length times quantity.
        """
        return self.length * self.quantity
