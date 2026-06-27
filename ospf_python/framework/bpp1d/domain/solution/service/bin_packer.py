"""装箱器 / Bin packer.

BPP1D 的首次适应装箱算法。
First-fit bin packing algorithm for BPP1D.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.framework.bpp1d.domain.item.model.bin import Bin
from ospf_python.framework.bpp1d.domain.item.model.packing_result import (
    PackingResult,
)
from ospf_python.framework.bpp1d.domain.solution.model.solution import (
    Solution,
)

if TYPE_CHECKING:
    from ospf_python.framework.bpp1d.domain.item.model.item import Item


@dataclass(frozen=True)
class BinPacker:
    """装箱器 / Bin packer.

    使用首次适应递减算法（FFD）求解一维装箱问题。
    Solves 1D bin packing using first-fit decreasing (FFD).

    Attributes:
        bin_capacity: 箱子容量 / Bin capacity.
    """

    bin_capacity: float = 0.0
    """箱子容量 / Bin capacity."""

    @staticmethod
    def create(
        *,
        bin_capacity: float,
    ) -> BinPacker:
        """创建装箱器 / Create packer.

        Args:
            bin_capacity: 箱子容量 / Bin capacity.

        Returns:
            装箱器实例 / BinPacker instance.
        """
        return BinPacker(bin_capacity=bin_capacity)

    def pack(
        self,
        items: tuple[Item, ...],
    ) -> Solution:
        """执行装箱 / Execute packing.

        使用首次适应递减算法将物品装入箱子。
        Packs items into bins using first-fit decreasing.

        Args:
            items: 待装箱物品 / Items to pack.

        Returns:
            装箱解 / Packing solution.
        """
        if not items:
            return Solution.create(solution_key="empty")

        sorted_items = tuple(sorted(items, key=lambda i: i.width, reverse=True))

        bins: list[Bin] = []
        results: list[PackingResult] = []

        for item in sorted_items:
            placed = False
            for idx, bin_ in enumerate(bins):
                if item.width <= bin_.remaining_capacity + 1e-9:
                    new_items = bin_.items + (item,)
                    position = bin_.used_capacity
                    bins[idx] = Bin.create(
                        bin_key=bin_.bin_key,
                        capacity=bin_.capacity,
                        items=new_items,
                    )
                    results.append(
                        PackingResult.create(
                            item=item,
                            bin_key=bin_.bin_key,
                            position=position,
                        )
                    )
                    placed = True
                    break

            if not placed:
                counter = len(bins)
                new_bin = Bin.create(
                    bin_key=f"bin_{counter}",
                    capacity=self.bin_capacity,
                    items=(item,),
                )
                bins.append(new_bin)
                results.append(
                    PackingResult.create(
                        item=item,
                        bin_key=new_bin.bin_key,
                        position=0.0,
                    ),
                )

        return Solution.create(
            solution_key="ffd_solution",
            bins=tuple(bins),
            objective_value=float(len(bins)),
        )

    def pack_with_results(
        self,
        items: tuple[Item, ...],
    ) -> tuple[Solution, tuple[PackingResult, ...]]:
        """执行装箱并返回详细结果 / Pack with detailed results.

        Args:
            items: 待装箱物品 / Items to pack.

        Returns:
            解和装箱结果元组 / Solution and packing results.
        """
        if not items:
            return (
                Solution.create(solution_key="empty"),
                (),
            )

        sorted_items = tuple(sorted(items, key=lambda i: i.width, reverse=True))

        bins: list[Bin] = []
        results: list[PackingResult] = []

        for item in sorted_items:
            placed = False
            for idx, bin_ in enumerate(bins):
                if item.width <= bin_.remaining_capacity + 1e-9:
                    new_items = bin_.items + (item,)
                    position = bin_.used_capacity
                    bins[idx] = Bin.create(
                        bin_key=bin_.bin_key,
                        capacity=bin_.capacity,
                        items=new_items,
                    )
                    results.append(
                        PackingResult.create(
                            item=item,
                            bin_key=bin_.bin_key,
                            position=position,
                        )
                    )
                    placed = True
                    break

            if not placed:
                counter = len(bins)
                new_bin = Bin.create(
                    bin_key=f"bin_{counter}",
                    capacity=self.bin_capacity,
                    items=(item,),
                )
                bins.append(new_bin)
                results.append(
                    PackingResult.create(
                        item=item,
                        bin_key=new_bin.bin_key,
                        position=0.0,
                    ),
                )

        solution = Solution.create(
            solution_key="ffd_solution",
            bins=tuple(bins),
            objective_value=float(len(bins)),
        )
        return (solution, tuple(results))
