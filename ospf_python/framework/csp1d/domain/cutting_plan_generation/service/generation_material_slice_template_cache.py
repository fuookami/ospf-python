"""CSP1D 材料切片模板缓存。

按材料缓存切片模板，避免重复生成。
Caches slice templates per material to avoid redundant generation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationMaterialSliceTemplateCache:
    """材料切片模板缓存 / Material slice template cache.

    为每种材料缓存已生成的切片模板，
    在多次生成请求中复用相同材料的模板。
    Caches generated slice templates for each material,
    reusing templates for the same material across
    multiple generation requests.

    Attributes:
        entries: 材料名称到切片模板的映射。
            Material name to slice template mapping.
    """

    entries: tuple[tuple[str, tuple[dict[str, int], ...]], ...] = ()
    """材料切片模板映射 / Material to slice template mapping."""

    def get(
        self,
        material: str,
    ) -> tuple[dict[str, int], ...] | None:
        """获取指定材料的切片模板。

        Get slice template for the specified material.

        Args:
            material: 材料名称。
                Material name.

        Returns:
            切片模板元组，不存在返回 None。
            Slice template tuple, None if not found.
        """
        return next(
            (templates for name, templates in self.entries if name == material),
            None,
        )

    def contains(self, material: str) -> bool:
        """检查是否包含指定材料的缓存。

        Check if cache contains the specified material.

        Args:
            material: 材料名称。
                Material name.

        Returns:
            包含返回 True / True if contained.
        """
        return any(name == material for name, _ in self.entries)

    def put(
        self,
        material: str,
        templates: tuple[dict[str, int], ...],
    ) -> GenerationMaterialSliceTemplateCache:
        """添加或更新材料切片模板。

        Add or update material slice template.

        Args:
            material: 材料名称。
                Material name.
            templates: 切片模板。
                Slice templates.

        Returns:
            包含新条目的缓存实例。
            Cache instance with new entry.
        """
        new_entries = tuple(
            (name, tpl) for name, tpl in self.entries if name != material
        ) + ((material, templates),)
        return GenerationMaterialSliceTemplateCache(entries=new_entries)

    @property
    def size(self) -> int:
        """获取缓存条目数。

        Get number of cached entries.

        Returns:
            缓存条目数量。
            Number of cache entries.
        """
        return len(self.entries)

    @property
    def is_empty(self) -> bool:
        """判断缓存是否为空。

        Check if cache is empty.

        Returns:
            无缓存条目时返回 True。
            True when no cache entries.
        """
        return len(self.entries) == 0
