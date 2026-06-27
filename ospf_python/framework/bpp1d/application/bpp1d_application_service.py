"""BPP1D 应用服务 / BPP1D application service.

BPP1D 的主编排服务。
Main orchestration service for BPP1D.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.framework.bpp1d.domain.item.item_context import (
    ItemContext,
)
from ospf_python.framework.bpp1d.domain.item.service.item_merger import (
    ItemMerger,
)
from ospf_python.framework.bpp1d.domain.solution.service.bin_packer import (
    BinPacker,
)
from ospf_python.framework.bpp1d.domain.solution.service.solution_validator import (
    SolutionValidator,
    ValidationReport,
)

if TYPE_CHECKING:
    from ospf_python.framework.bpp1d.domain.constraint.model.constraint import (
        Constraint,
    )
    from ospf_python.framework.bpp1d.domain.item.model.item import Item
    from ospf_python.framework.bpp1d.domain.solution.model.solution import (
        Solution,
    )


@dataclass(frozen=True)
class PackingRequest:
    """装箱请求 / Packing request.

    描述一次装箱请求的参数。
    Describes parameters for a packing request.

    Attributes:
        bin_capacity: 箱子容量 / Bin capacity.
        items: 待装箱物品 / Items to pack.
        constraints: 装箱约束 / Packing constraints.
    """

    bin_capacity: float
    """箱子容量 / Bin capacity."""

    items: tuple[Item, ...] = ()
    """待装箱物品 / Items to pack."""

    constraints: tuple[Constraint, ...] = ()
    """装箱约束 / Packing constraints."""

    @staticmethod
    def create(
        *,
        bin_capacity: float,
        items: tuple[Item, ...] = (),
        constraints: tuple[Constraint, ...] = (),
    ) -> PackingRequest:
        """创建装箱请求 / Create packing request.

        Args:
            bin_capacity: 箱子容量 / Bin capacity.
            items: 待装箱物品，默认空 /
                Items to pack, default empty.
            constraints: 装箱约束，默认空 /
                Packing constraints, default empty.

        Returns:
            装箱请求实例 / PackingRequest instance.
        """
        return PackingRequest(
            bin_capacity=bin_capacity,
            items=items,
            constraints=constraints,
        )


@dataclass(frozen=True)
class PackingResponse:
    """装箱响应 / Packing response.

    描述一次装箱的结果。
    Describes the result of a packing operation.

    Attributes:
        solution: 装箱解 / Packing solution.
        report: 验证报告 / Validation report.
        item_context: 物品上下文 / Item context.
    """

    solution: Solution
    """装箱解 / Packing solution."""

    report: ValidationReport = None
    """验证报告 / Validation report."""

    item_context: ItemContext = None
    """物品上下文 / Item context."""

    def __post_init__(self) -> None:
        """初始化后处理 / Post-init handler.

        设置默认值。
        Sets default values.
        """
        if self.report is None:
            object.__setattr__(
                self,
                "report",
                ValidationReport.ok(),
            )
        if self.item_context is None:
            object.__setattr__(
                self,
                "item_context",
                ItemContext.create(),
            )

    @staticmethod
    def create(
        *,
        solution: Solution,
        report: ValidationReport | None = None,
        item_context: ItemContext | None = None,
    ) -> PackingResponse:
        """创建装箱响应 / Create packing response.

        Args:
            solution: 装箱解 / Packing solution.
            report: 验证报告，默认通过 /
                Validation report, default ok.
            item_context: 物品上下文，默认空 /
                Item context, default empty.

        Returns:
            装箱响应实例 / PackingResponse instance.
        """
        return PackingResponse(
            solution=solution,
            report=report or ValidationReport.ok(),
            item_context=item_context or ItemContext.create(),
        )

    @property
    def is_valid(self) -> bool:
        """是否有效 / Whether valid.

        Returns:
            验证报告是否通过。
            Whether validation report passed.
        """
        return self.report.valid


@dataclass(frozen=True)
class Bpp1dApplicationService:
    """BPP1D 应用服务 / BPP1D application service.

    编排装箱流程：注册物品、合并、装箱、验证。
    Orchestrates packing flow: register, merge, pack, validate.

    Attributes:
        merger: 物品合并器 / Item merger.
        packer: 装箱器 / Bin packer.
        validator: 解验证器 / Solution validator.
        item_context: 物品上下文 / Item context.
    """

    merger: ItemMerger = None
    """物品合并器 / Item merger."""

    packer: BinPacker = None
    """装箱器 / Bin packer."""

    validator: SolutionValidator = None
    """解验证器 / Solution validator."""

    item_context: ItemContext = None
    """物品上下文 / Item context."""

    def __post_init__(self) -> None:
        """初始化后处理 / Post-init handler.

        设置默认组件。
        Sets default components.
        """
        if self.merger is None:
            object.__setattr__(self, "merger", ItemMerger.create())
        if self.validator is None:
            object.__setattr__(self, "validator", SolutionValidator.create())
        if self.item_context is None:
            object.__setattr__(self, "item_context", ItemContext.create())

    @staticmethod
    def create(
        *,
        bin_capacity: float,
    ) -> Bpp1dApplicationService:
        """创建应用服务 / Create application service.

        Args:
            bin_capacity: 箱子容量 / Bin capacity.

        Returns:
            应用服务实例 / Bpp1dApplicationService instance.
        """
        return Bpp1dApplicationService(
            packer=BinPacker.create(bin_capacity=bin_capacity),
        )

    def execute(
        self,
        request: PackingRequest,
    ) -> PackingResponse:
        """执行装箱 / Execute packing.

        完整流程：注册 -> 合并 -> 装箱 -> 验证。
        Full flow: register -> merge -> pack -> validate.

        Args:
            request: 装箱请求 / Packing request.

        Returns:
            装箱响应 / Packing response.
        """
        context = self.item_context.register_many(request.items)

        merged = self.merger.merge_duplicates(context.get_all())

        packer = BinPacker.create(bin_capacity=request.bin_capacity)
        solution = packer.pack(merged)

        report = self.validator.validate(
            solution=solution,
            items=merged,
            constraints=request.constraints,
        )

        return PackingResponse.create(
            solution=solution,
            report=report,
            item_context=context,
        )
