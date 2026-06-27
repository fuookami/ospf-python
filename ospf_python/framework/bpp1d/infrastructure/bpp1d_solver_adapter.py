"""BPP1D 求解器适配器 / BPP1D solver adapter.

将 BPP1D 领域模型转换为求解器输入。
Converts BPP1D domain models to solver input.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.framework.bpp1d.domain.item.model.item import Item
from ospf_python.framework.bpp1d.domain.solution.service.bin_packer import (
    BinPacker,
)
from ospf_python.framework.bpp1d.infrastructure.bpp1d_dto import (
    Bpp1dInputDto,
    Bpp1dOutputDto,
    ItemDto,
)

if TYPE_CHECKING:
    from ospf_python.framework.bpp1d.domain.solution.model.solution import (
        Solution,
    )


@dataclass(frozen=True)
class Bpp1dSolverAdapter:
    """BPP1D 求解器适配器 / BPP1D solver adapter.

    在 DTO 和领域模型之间进行转换。
    Translates between DTOs and domain models.

    Attributes:
        packer: 装箱器 / Bin packer.
    """

    packer: BinPacker = None
    """装箱器 / Bin packer."""

    def __post_init__(self) -> None:
        """初始化后处理 / Post-init handler.

        设置默认装箱器。
        Sets default packer.
        """
        if self.packer is None:
            object.__setattr__(
                self,
                "packer",
                BinPacker.create(bin_capacity=1.0),
            )

    @staticmethod
    def create(
        *,
        bin_capacity: float,
    ) -> Bpp1dSolverAdapter:
        """创建适配器 / Create adapter.

        Args:
            bin_capacity: 箱子容量 / Bin capacity.

        Returns:
            适配器实例 / Bpp1dSolverAdapter instance.
        """
        return Bpp1dSolverAdapter(
            packer=BinPacker.create(
                bin_capacity=bin_capacity,
            ),
        )

    def solve(
        self,
        input_dto: Bpp1dInputDto,
    ) -> Bpp1dOutputDto:
        """求解 / Solve.

        将输入 DTO 转换为领域模型，执行求解，
        并将结果转换为输出 DTO。
        Converts input DTO to domain model, solves,
        and converts result to output DTO.

        Args:
            input_dto: 输入 DTO / Input DTO.

        Returns:
            输出 DTO / Output DTO.
        """
        items = self._items_from_dto(input_dto.items)
        solution = self.packer.pack(items)
        return self._solution_to_dto(solution)

    def _items_from_dto(
        self,
        dtos: tuple[ItemDto, ...],
    ) -> tuple[Item, ...]:
        """DTO 转物品 / DTOs to items.

        Args:
            dtos: 物品 DTO 列表 / Item DTO list.

        Returns:
            物品元组 / Items tuple.
        """
        return tuple(
            Item.create(
                item_key=dto.item_key,
                width=dto.width,
                height=dto.height,
                weight=dto.weight,
            )
            for dto in dtos
        )

    def _solution_to_dto(
        self,
        solution: Solution,
    ) -> Bpp1dOutputDto:
        """解转 DTO / Solution to DTO.

        Args:
            solution: 装箱解 / Packing solution.

        Returns:
            输出 DTO / Output DTO.
        """
        bin_dtos = tuple(
            Bpp1dOutputDto.BinDto(
                bin_key=bin_.bin_key,
                item_keys=tuple(i.item_key for i in bin_.items),
                used_capacity=bin_.used_capacity,
            )
            for bin_ in solution.bins
        )
        return Bpp1dOutputDto(
            solution_key=solution.solution_key,
            bins=bin_dtos,
            bin_count=solution.bin_count,
            objective_value=solution.objective_value,
        )
