"""CSP1D 领域值转换。

在领域对象与外部表示之间进行值转换。
Converts values between domain objects and external representations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DomainValueConversion:
    """领域值转换器 / Domain value converter.

    提供 CSP1D 领域中常用的值转换功能，
    包括宽度与索引之间的映射、名称规范化等。
    Provides common value conversion utilities in
    the CSP1D domain, including width-to-index mapping
    and name normalization.

    Attributes:
        width_to_index: 宽度到索引的映射。
            Width to index mapping.
        name_to_width: 名称到宽度的映射。
            Name to width mapping.
    """

    width_to_index: tuple[tuple[float, int], ...] = ()
    """宽度到索引的映射 / Width to index mapping."""

    name_to_width: tuple[tuple[str, float], ...] = ()
    """名称到宽度的映射 / Name to width mapping."""

    @staticmethod
    def from_materials(
        *,
        materials: tuple[tuple[str, float], ...],
    ) -> DomainValueConversion:
        """从材料信息创建转换器。

        Create converter from material info.

        Args:
            materials: (材料名称, 宽度) 元组。
                (material_name, width) tuples.

        Returns:
            域值转换器实例。
            Domain value converter instance.
        """
        sorted_mats = sorted(materials, key=lambda x: x[1])
        width_index = tuple(
            (width, idx) for idx, (_, width) in enumerate(sorted_mats)
        )
        name_width = tuple(sorted_mats)
        return DomainValueConversion(
            width_to_index=width_index,
            name_to_width=name_width,
        )

    def width_of(self, name: str) -> float | None:
        """获取材料名称对应的宽度。

        Get width for the material name.

        Args:
            name: 材料名称。
                Material name.

        Returns:
            宽度值，不存在返回 None。
            Width value, None if not found.
        """
        return next(
            (width for mat_name, width in self.name_to_width if mat_name == name),
            None,
        )

    def index_of_width(self, width: float) -> int | None:
        """获取宽度对应的索引。

        Get index for the width.

        Args:
            width: 宽度值。
                Width value.

        Returns:
            索引值，不存在返回 None。
            Index value, None if not found.
        """
        return next(
            (idx for w, idx in self.width_to_index if abs(w - width) < 1e-8),
            None,
        )

    def name_for_index(self, index: int) -> str | None:
        """获取索引对应的材料名称。

        Get material name for the index.

        Args:
            index: 索引值。
                Index value.

        Returns:
            材料名称，索引越界返回 None。
            Material name, None if index out of range.
        """
        if 0 <= index < len(self.name_to_width):
            return self.name_to_width[index][0]
        out_of_range_result = None
        return out_of_range_result

    @property
    def size(self) -> int:
        """获取转换器条目数。

        Get number of converter entries.

        Returns:
            条目数量。
            Number of entries.
        """
        return len(self.name_to_width)

    @property
    def is_empty(self) -> bool:
        """判断转换器是否为空。

        Check if converter is empty.

        Returns:
            无条目时返回 True。
            True when no entries.
        """
        return len(self.name_to_width) == 0

    def sorted_widths(self) -> tuple[float, ...]:
        """获取排序后的所有宽度。

        Get all widths sorted ascending.

        Returns:
            升序排列的宽度元组。
            Tuple of widths sorted ascending.
        """
        return tuple(w for w, _ in self.width_to_index)
