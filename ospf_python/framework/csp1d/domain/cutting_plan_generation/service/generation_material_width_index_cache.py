"""CSP1D 材料宽度索引缓存。

缓存材料宽度到索引的映射，加速宽度查找。
Caches material width to index mapping for fast width lookup.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationMaterialWidthIndexCache:
    """材料宽度索引缓存 / Material width index cache.

    维护材料名称到宽度索引的映射，
    用于在生成过程中快速定位材料。
    Maintains material name to width index mapping
    for fast material lookup during generation.

    Attributes:
        width_map: 材料名称到宽度的映射。
            Material name to width mapping.
        index_map: 材料名称到索引的映射。
            Material name to index mapping.
    """

    width_map: tuple[tuple[str, float], ...] = ()
    """材料名称到宽度的映射 / Material name to width mapping."""

    index_map: tuple[tuple[str, int], ...] = ()
    """材料名称到索引的映射 / Material name to index mapping."""

    def get_width(self, material: str) -> float | None:
        """获取指定材料的宽度。

        Get width for the specified material.

        Args:
            material: 材料名称。
                Material name.

        Returns:
            材料宽度，不存在返回 None。
            Material width, None if not found.
        """
        return next(
            (width for name, width in self.width_map if name == material),
            None,
        )

    def get_index(self, material: str) -> int | None:
        """获取指定材料的索引。

        Get index for the specified material.

        Args:
            material: 材料名称。
                Material name.

        Returns:
            材料索引，不存在返回 None。
            Material index, None if not found.
        """
        return next(
            (idx for name, idx in self.index_map if name == material),
            None,
        )

    def put(
        self,
        material: str,
        width: float,
        index: int,
    ) -> GenerationMaterialWidthIndexCache:
        """添加或更新材料宽度索引。

        Add or update material width index.

        Args:
            material: 材料名称。
                Material name.
            width: 材料宽度。
                Material width.
            index: 材料索引。
                Material index.

        Returns:
            包含新条目的缓存实例。
            Cache instance with new entry.
        """
        new_width_map = tuple(
            (n, w) for n, w in self.width_map if n != material
        ) + ((material, width),)
        new_index_map = tuple(
            (n, i) for n, i in self.index_map if n != material
        ) + ((material, index),)
        return GenerationMaterialWidthIndexCache(
            width_map=new_width_map,
            index_map=new_index_map,
        )

    def contains(self, material: str) -> bool:
        """检查是否包含指定材料。

        Check if cache contains the specified material.

        Args:
            material: 材料名称。
                Material name.

        Returns:
            包含返回 True / True if contained.
        """
        return any(name == material for name, _ in self.width_map)

    @property
    def size(self) -> int:
        """获取缓存条目数。

        Get number of cached entries.

        Returns:
            缓存条目数量。
            Number of cache entries.
        """
        return len(self.width_map)

    def sorted_by_width(self) -> tuple[tuple[str, float], ...]:
        """按宽度排序返回所有材料。

        Get all materials sorted by width.

        Returns:
            按宽度升序排列的材料元组。
            Tuple of materials sorted by width ascending.
        """
        return tuple(sorted(self.width_map, key=lambda item: item[1]))
