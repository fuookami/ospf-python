"""BPP1D 数据传输对象 / BPP1D DTOs.

BPP1D 的输入输出数据传输对象。
Input/output data transfer objects for BPP1D.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ItemDto:
    """物品 DTO / Item DTO.

    描述物品的传输数据。
    Describes item transfer data.

    Attributes:
        item_key: 物品键 / Item key.
        width: 物品宽度 / Item width.
        height: 物品高度 / Item height.
        weight: 物品重量 / Item weight.
    """

    item_key: str
    """物品键 / Item key."""

    width: float
    """物品宽度 / Item width."""

    height: float
    """物品高度 / Item height."""

    weight: float = 0.0
    """物品重量，默认 0 / Item weight, default 0."""

    @staticmethod
    def create(
        *,
        item_key: str,
        width: float,
        height: float,
        weight: float = 0.0,
    ) -> ItemDto:
        """创建物品 DTO / Create item DTO.

        Args:
            item_key: 物品键 / Item key.
            width: 物品宽度 / Item width.
            height: 物品高度 / Item height.
            weight: 物品重量，默认 0 / Weight, default 0.

        Returns:
            物品 DTO 实例 / ItemDto instance.
        """
        return ItemDto(
            item_key=item_key,
            width=width,
            height=height,
            weight=weight,
        )


@dataclass(frozen=True)
class ConstraintDto:
    """约束 DTO / Constraint DTO.

    描述约束的传输数据。
    Describes constraint transfer data.

    Attributes:
        constraint_key: 约束键 / Constraint key.
        constraint_type: 约束类型 / Constraint type.
        item_keys: 受约束物品键 / Constrained item keys.
        max_value: 约束上界 / Constraint upper bound.
    """

    constraint_key: str
    """约束键 / Constraint key."""

    constraint_type: str
    """约束类型 / Constraint type."""

    item_keys: tuple[str, ...] = ()
    """受约束物品键 / Constrained item keys."""

    max_value: float = 0.0
    """约束上界 / Constraint upper bound."""

    @staticmethod
    def create(
        *,
        constraint_key: str,
        constraint_type: str,
        item_keys: tuple[str, ...] = (),
        max_value: float = 0.0,
    ) -> ConstraintDto:
        """创建约束 DTO / Create constraint DTO.

        Args:
            constraint_key: 约束键 / Constraint key.
            constraint_type: 约束类型 / Constraint type.
            item_keys: 受约束物品键，默认空 /
                Constrained item keys, default empty.
            max_value: 约束上界，默认 0 /
                Constraint upper bound, default 0.

        Returns:
            约束 DTO 实例 / ConstraintDto instance.
        """
        return ConstraintDto(
            constraint_key=constraint_key,
            constraint_type=constraint_type,
            item_keys=item_keys,
            max_value=max_value,
        )


@dataclass(frozen=True)
class Bpp1dInputDto:
    """BPP1D 输入 DTO / BPP1D input DTO.

    描述装箱请求的输入数据。
    Describes input data for a packing request.

    Attributes:
        bin_capacity: 箱子容量 / Bin capacity.
        items: 物品列表 / Items list.
        constraints: 约束列表 / Constraints list.
    """

    bin_capacity: float
    """箱子容量 / Bin capacity."""

    items: tuple[ItemDto, ...] = ()
    """物品列表 / Items list."""

    constraints: tuple[ConstraintDto, ...] = ()
    """约束列表 / Constraints list."""

    @staticmethod
    def create(
        *,
        bin_capacity: float,
        items: tuple[ItemDto, ...] = (),
        constraints: tuple[ConstraintDto, ...] = (),
    ) -> Bpp1dInputDto:
        """创建输入 DTO / Create input DTO.

        Args:
            bin_capacity: 箱子容量 / Bin capacity.
            items: 物品列表，默认空 / Items list, default empty.
            constraints: 约束列表，默认空 /
                Constraints list, default empty.

        Returns:
            输入 DTO 实例 / Bpp1dInputDto instance.
        """
        return Bpp1dInputDto(
            bin_capacity=bin_capacity,
            items=items,
            constraints=constraints,
        )


@dataclass(frozen=True)
class Bpp1dOutputDto:
    """BPP1D 输出 DTO / BPP1D output DTO.

    描述装箱结果的输出数据。
    Describes output data for a packing result.

    Attributes:
        solution_key: 解键 / Solution key.
        bins: 箱子结果列表 / Bin results list.
        bin_count: 箱子数量 / Bin count.
        objective_value: 目标函数值 / Objective value.
    """

    @dataclass(frozen=True)
    class BinDto:
        """箱子结果 DTO / Bin result DTO.

        描述单个箱子的装箱结果。
        Describes packing result for a single bin.

        Attributes:
            bin_key: 箱子键 / Bin key.
            item_keys: 已装入物品键 / Packed item keys.
            used_capacity: 已用容量 / Used capacity.
        """

        bin_key: str
        """箱子键 / Bin key."""

        item_keys: tuple[str, ...] = ()
        """已装入物品键 / Packed item keys."""

        used_capacity: float = 0.0
        """已用容量 / Used capacity."""

    solution_key: str = ""
    """解键 / Solution key."""

    bins: tuple[BinDto, ...] = field(
        default_factory=tuple,
    )
    """箱子结果列表 / Bin results list."""

    bin_count: int = 0
    """箱子数量 / Bin count."""

    objective_value: float = 0.0
    """目标函数值 / Objective value."""

    @staticmethod
    def create(
        *,
        solution_key: str = "",
        bins: tuple[Bpp1dOutputDto.BinDto, ...] = (),
        bin_count: int = 0,
        objective_value: float = 0.0,
    ) -> Bpp1dOutputDto:
        """创建输出 DTO / Create output DTO.

        Args:
            solution_key: 解键，默认空 / Solution key, default empty.
            bins: 箱子结果，默认空 / Bin results, default empty.
            bin_count: 箱子数量，默认 0 / Bin count, default 0.
            objective_value: 目标值，默认 0 /
                Objective value, default 0.

        Returns:
            输出 DTO 实例 / Bpp1dOutputDto instance.
        """
        return Bpp1dOutputDto(
            solution_key=solution_key,
            bins=bins,
            bin_count=bin_count,
            objective_value=objective_value,
        )
