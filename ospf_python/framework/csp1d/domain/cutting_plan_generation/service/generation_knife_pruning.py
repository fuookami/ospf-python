"""CSP1D 刀数剪枝。

根据刀数限制对搜索空间进行剪枝。
Knife-based pruning for cutting plan generation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationKnifePruning:
    """刀数剪枝 / Knife pruning.

    在 DFS 或穷举生成过程中，根据当前已用刀数
    和最大刀数限制决定是否剪枝。
    During DFS or exhaustive generation, decides
    whether to prune based on current knife count
    and maximum knife limit.

    Attributes:
        max_knife_count: 最大允许刀数。
            Maximum allowed knife count.
    """

    max_knife_count: int = 0
    """最大允许刀数 / Maximum allowed knife count."""

    def should_prune(self, current_knife_count: int) -> bool:
        """判断是否应剪枝。

        Determine whether to prune.

        Args:
            current_knife_count: 当前已用刀数。
                Current knife count used.

        Returns:
            超过限制返回 True / True if exceeds limit.
        """
        if self.max_knife_count <= 0:
            return False
        return current_knife_count >= self.max_knife_count

    def remaining_knives(self, current_knife_count: int) -> int:
        """计算剩余可用刀数。

        Calculate remaining available knives.

        Args:
            current_knife_count: 当前已用刀数。
                Current knife count used.

        Returns:
            剩余刀数（非负）。
            Remaining knives (non-negative).
        """
        if self.max_knife_count <= 0:
            return 0
        return max(0, self.max_knife_count - current_knife_count)

    def can_add_cuts(
        self,
        current_knife_count: int,
        additional_cuts: int,
    ) -> bool:
        """判断能否增加指定数量的切割。

        Check if additional cuts can be added.

        Args:
            current_knife_count: 当前已用刀数。
                Current knife count.
            additional_cuts: 拟增加的切割数。
                Additional cuts to add.

        Returns:
            可以增加返回 True / True if can add.
        """
        if self.max_knife_count <= 0:
            return True
        return current_knife_count + additional_cuts <= self.max_knife_count
