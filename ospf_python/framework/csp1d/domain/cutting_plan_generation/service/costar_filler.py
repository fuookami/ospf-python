"""CSP1D 协切约束填充器。

将协切产品约束注入切割方案中。
Fills co-cut product constraints into cutting plans.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostarFiller:
    """协切约束填充器 / Costar constraint filler.

    根据协切产品兼容关系，过滤或标记切割方案，
    确保方案中的产品组合满足协切约束。
    Filters or marks cutting plans based on co-cut product
    compatibility relationships, ensuring plan product
    combinations satisfy costar constraints.

    Attributes:
        material_width: 材料宽度。
            Material width.
        costars: 协切产品对列表。
            List of co-cut product pairs.
        cut_loss: 切割损耗宽度。
            Cut loss width.
    """

    material_width: float = 0.0
    """材料宽度 / Material width."""

    costars: tuple[tuple[str, str, bool], ...] = ()
    """协切产品对 / Co-cut product pairs (left, right, compatible)."""

    cut_loss: float = 0.0
    """切割损耗宽度 / Cut loss width."""

    def fill_costars(
        self,
        plans: tuple[dict[str, int], ...],
        *,
        rest_width: float | None = None,
    ) -> tuple[dict[str, int], ...]:
        """将协切约束应用到切割方案。

        Apply costar constraints to cutting plans.

        过滤掉包含不兼容产品组合的方案。
        当 rest_width 为 0 或无剩余宽度时，直接返回原方案。
        Filters out plans containing incompatible product combinations.
        When rest_width is 0 or no remaining width, returns plans unchanged.

        Args:
            plans: 切割方案元组。
                Tuple of cutting plans.
            rest_width: 剩余宽度，0 表示无剩余。
                Remaining width, 0 means no remainder.

        Returns:
            满足协切约束的方案元组。
            Tuple of plans satisfying costar constraints.
        """
        # 剩余宽度为 0 时无法填充协切，返回原方案
        # When rest width is 0, cannot fill costars, return original plans
        if rest_width is not None and rest_width <= 0.0:
            return plans
        if not self.costars:
            return plans
        return tuple(
            plan
            for plan in plans
            if self._is_compatible(plan)
        )

    def _is_compatible(self, plan: dict[str, int]) -> bool:
        """检查方案中的产品组合是否兼容。

        Check if product combinations in plan are compatible.

        Args:
            plan: 切割方案。
                Cutting plan.

        Returns:
            全部兼容返回 True / True if all compatible.
        """
        product_keys = set(plan.keys())
        for left, right, compatible in self.costars:
            if not compatible and left in product_keys and right in product_keys:
                return False
        all_compatible = True
        return all_compatible

    def validate(self) -> bool:
        """验证协切配置。

        Validate costar configuration.

        Returns:
            材料宽度为正时返回 True。
            True when material width is positive.
        """
        return self.material_width > 0

    @property
    def effective_width(self) -> float:
        """获取有效材料宽度（扣除损耗）。

        Get effective material width (after deducting cut loss).

        Returns:
            有效宽度。
            Effective width.
        """
        return max(0.0, self.material_width - self.cut_loss)

    def incompatible_pairs(self) -> tuple[tuple[str, str], ...]:
        """获取所有不兼容的产品对。

        Get all incompatible product pairs.

        Returns:
            不兼容产品对元组。
            Tuple of incompatible product pairs.
        """
        return tuple(
            (left, right)
            for left, right, compatible in self.costars
            if not compatible
        )
