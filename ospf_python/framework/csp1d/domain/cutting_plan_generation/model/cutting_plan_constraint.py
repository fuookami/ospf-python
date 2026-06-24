"""CSP1D 单条切割方案约束。

描述切割方案需要满足的单项约束条件。
Single constraint for cutting plan generation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CuttingPlanConstraint:
    """单条切割方案约束 / Single cutting plan constraint.

    描述切割方案生成过程中的一项具体约束，
    包括产品需求、材料限制或刀具限制。
    Describes a specific constraint during cutting plan
    generation, covering product demand, material limits,
    or knife limits.

    Attributes:
        product_key: 产品标识 / Product identifier.
        min_quantity: 最小切割数量 / Minimum cut quantity.
        max_quantity: 最大切割数量 / Maximum cut quantity.
        width: 产品宽度 / Product width.
        length: 产品长度 / Product length.
    """

    product_key: str = ""
    """产品标识 / Product identifier."""

    min_quantity: int = 0
    """最小切割数量 / Minimum cut quantity."""

    max_quantity: int = 0
    """最大切割数量 / Maximum cut quantity."""

    width: float = 0.0
    """产品宽度 / Product width."""

    length: float = 0.0
    """产品长度 / Product length."""

    @property
    def is_active(self) -> bool:
        """判断约束是否活跃。

        Check if constraint is active.

        Returns:
            最小数量大于 0 时为活跃。
            Active when min quantity > 0.
        """
        return self.min_quantity > 0

    @property
    def quantity_range(self) -> tuple[int, int]:
        """获取数量范围。

        Get quantity range.

        Returns:
            (最小数量, 最大数量) 元组。
            (min_quantity, max_quantity) tuple.
        """
        return (self.min_quantity, self.max_quantity)

    def is_satisfied_by(self, quantity: int) -> bool:
        """检查给定数量是否满足约束。

        Check if the given quantity satisfies the constraint.

        Args:
            quantity: 待检查的数量 / Quantity to check.

        Returns:
            满足返回 True / True if satisfied.
        """
        return self.min_quantity <= quantity <= self.max_quantity
