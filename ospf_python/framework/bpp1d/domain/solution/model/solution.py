"""解定义 / Solution definition.

BPP1D 的装箱解定义。
Packing solution definition for BPP1D.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp1d.domain.item.model.bin import Bin


@dataclass(frozen=True)
class Solution:
    """解 / Solution.

    描述 BPP1D 的完整装箱方案。
    Describes a complete packing solution for BPP1D.

    Attributes:
        solution_key: 解键 / Solution key.
        bins: 使用的箱子列表 / List of bins used.
        objective_value: 目标函数值 / Objective function value.
    """

    solution_key: str
    """解键 / Solution key."""

    bins: tuple[Bin, ...] = field(
        default_factory=tuple,
    )
    """使用的箱子列表 / List of bins used."""

    objective_value: float = 0.0
    """目标函数值，默认 0 / Objective value, default 0."""

    @staticmethod
    def create(
        *,
        solution_key: str,
        bins: tuple[Bin, ...] = (),
        objective_value: float = 0.0,
    ) -> Solution:
        """创建解 / Create solution.

        Args:
            solution_key: 解键 / Solution key.
            bins: 箱子列表，默认空 / Bins list, default empty.
            objective_value: 目标值，默认 0 /
                Objective value, default 0.

        Returns:
            解实例 / Solution instance.
        """
        return Solution(
            solution_key=solution_key,
            bins=bins,
            objective_value=objective_value,
        )

    @property
    def bin_count(self) -> int:
        """箱子数量 / Bin count.

        Returns:
            解中使用的箱子数量。
            Number of bins used in the solution.
        """
        return len(self.bins)

    @property
    def total_items(self) -> int:
        """总物品数 / Total items.

        Returns:
            所有箱子中物品数量之和。
            Sum of item counts across all bins.
        """
        return sum(bin.item_count for bin in self.bins)

    @property
    def total_weight(self) -> float:
        """总重量 / Total weight.

        Returns:
            所有箱子中物品重量之和。
            Sum of weights across all bins.
        """
        return sum(bin.total_weight for bin in self.bins)

    @property
    def average_fill_rate(self) -> float:
        """平均填充率 / Average fill rate.

        Returns:
            所有箱子的平均容量利用率。
            Average capacity utilization across all bins.
        """
        if not self.bins:
            return 0.0
        rates = tuple(
            bin.used_capacity / bin.capacity for bin in self.bins if bin.capacity > 0.0
        )
        return sum(rates) / len(rates) if rates else 0.0
