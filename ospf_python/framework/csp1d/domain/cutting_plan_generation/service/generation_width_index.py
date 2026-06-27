"""CSP1D 宽度索引。

提供基于宽度的产品/材料快速查找。
Provides width-based fast lookup for products/materials.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationWidthIndex:
    """宽度索引 / Width index.

    按宽度建立索引，支持按宽度范围查询产品或材料。
    在切割方案生成过程中用于快速筛选适配宽度的产品。
    Indexes by width, supporting range queries for products
    or materials. Used during cutting plan generation to
    quickly filter products matching a width.

    Attributes:
        entries: 宽度到键列表的有序映射。
            Sorted mapping of width to key lists.
        precision: 数值比较精度。
            Numerical comparison precision.
    """

    entries: tuple[tuple[float, tuple[str, ...]], ...] = ()
    """宽度到键的映射 / Width to keys mapping."""

    precision: float = 1e-8
    """数值精度 / Numerical precision."""

    def get_keys_at(self, width: float) -> tuple[str, ...]:
        """获取指定宽度的所有键。

        Get all keys at the specified width.

        Args:
            width: 目标宽度。
                Target width.

        Returns:
            匹配的键元组，不存在返回空元组。
            Tuple of matching keys, empty if none.
        """
        for w, keys in self.entries:
            if abs(w - width) <= self.precision:
                return keys
        return ()

    def get_keys_in_range(
        self,
        min_width: float,
        max_width: float,
    ) -> tuple[str, ...]:
        """获取宽度范围内的所有键。

        Get all keys within the width range.

        Args:
            min_width: 最小宽度。
                Minimum width.
            max_width: 最大宽度。
                Maximum width.

        Returns:
            范围内所有键的元组。
            Tuple of all keys in range.
        """
        result: list[str] = []
        for w, keys in self.entries:
            if min_width - self.precision <= w <= max_width + self.precision:
                result.extend(keys)
        return tuple(result)

    def add(
        self,
        width: float,
        key: str,
    ) -> GenerationWidthIndex:
        """添加宽度-键条目。

        Add width-key entry.

        Args:
            width: 宽度。
                Width.
            key: 键。
                Key.

        Returns:
            包含新条目的索引实例。
            Index instance with new entry.
        """
        for i, (w, keys) in enumerate(self.entries):
            if abs(w - width) <= self.precision:
                if key in keys:
                    return self
                new_keys = keys + (key,)
                new_entries = (
                    self.entries[:i]
                    + ((w, new_keys),)
                    + self.entries[i + 1:]
                )
                return GenerationWidthIndex(
                    entries=new_entries,
                    precision=self.precision,
                )
        new_entries = self.entries + ((width, (key,)),)
        return GenerationWidthIndex(
            entries=new_entries,
            precision=self.precision,
        )

    def contains_key(self, key: str) -> bool:
        """检查是否包含指定键。

        Check if index contains the specified key.

        Args:
            key: 键。
                Key.

        Returns:
            包含返回 True / True if contained.
        """
        return any(key in keys for _, keys in self.entries)

    @property
    def total_keys(self) -> int:
        """获取所有键的总数。

        Get total number of all keys.

        Returns:
            键总数。
            Total number of keys.
        """
        return sum(len(keys) for _, keys in self.entries)

    @property
    def width_count(self) -> int:
        """获取不同宽度的数量。

        Get number of distinct widths.

        Returns:
            不同宽度数。
            Number of distinct widths.
        """
        return len(self.entries)

    @property
    def sorted_widths(self) -> tuple[float, ...]:
        """获取排序后的所有宽度。

        Get all widths sorted ascending.

        Returns:
            按升序排列的宽度元组。
            Tuple of widths sorted ascending.
        """
        return tuple(w for w, _ in self.entries)
