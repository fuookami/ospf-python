"""CSP1D 并发材料切片模板缓存。

线程安全的材料切片模板缓存包装，用于并行方案生成。
Thread-safe material slice template cache wrapper
for parallel plan generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_material_slice_template_cache import (
    GenerationMaterialSliceTemplateCache,
)


@dataclass(frozen=True)
class ConcurrentGenerationMaterialSliceTemplateCache:
    """并发材料切片模板缓存 / Concurrent material slice template cache.

    在并行切割方案生成过程中，为每种材料缓存切片模板。
    通过快照机制保证不可变性，支持安全的并发读取。
    Caches slice templates per material during parallel
    cutting plan generation. Ensures immutability through
    snapshot mechanism, supporting safe concurrent reads.

    Attributes:
        cache: 底层材料切片模板缓存。
            Underlying material slice template cache.
        hit_count: 缓存命中次数。
            Cache hit count.
        miss_count: 缓存未命中次数。
            Cache miss count.
    """

    cache: GenerationMaterialSliceTemplateCache = field(
        default_factory=GenerationMaterialSliceTemplateCache,
    )
    """底层缓存 / Underlying cache."""

    hit_count: int = 0
    """命中次数 / Hit count."""

    miss_count: int = 0
    """未命中次数 / Miss count."""

    def get(
        self,
        material: str,
    ) -> tuple[dict[str, int], ...] | None:
        """获取指定材料的切片模板，同时更新命中统计。

        Get slice template for the specified material,
        updating hit/miss statistics.

        Args:
            material: 材料名称。
                Material name.

        Returns:
            切片模板元组，不存在返回 None。
            Slice template tuple, None if not found.
        """
        result = self.cache.get(material)
        return result

    def put(
        self,
        material: str,
        templates: tuple[dict[str, int], ...],
    ) -> ConcurrentGenerationMaterialSliceTemplateCache:
        """添加材料切片模板，返回新缓存实例。

        Add material slice template, return new cache instance.

        Args:
            material: 材料名称。
                Material name.
            templates: 切片模板。
                Slice templates.

        Returns:
            包含新模板的缓存实例。
            Cache instance with new template.
        """
        new_cache = self.cache.put(material, templates)
        return ConcurrentGenerationMaterialSliceTemplateCache(
            cache=new_cache,
            hit_count=self.hit_count,
            miss_count=self.miss_count,
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
        return self.cache.contains(material)

    def record_hit(self) -> ConcurrentGenerationMaterialSliceTemplateCache:
        """记录一次缓存命中，返回新实例。

        Record a cache hit, return new instance.

        Returns:
            更新命中计数的缓存实例。
            Cache instance with updated hit count.
        """
        return ConcurrentGenerationMaterialSliceTemplateCache(
            cache=self.cache,
            hit_count=self.hit_count + 1,
            miss_count=self.miss_count,
        )

    def record_miss(self) -> ConcurrentGenerationMaterialSliceTemplateCache:
        """记录一次缓存未命中，返回新实例。

        Record a cache miss, return new instance.

        Returns:
            更新未命中计数的缓存实例。
            Cache instance with updated miss count.
        """
        return ConcurrentGenerationMaterialSliceTemplateCache(
            cache=self.cache,
            hit_count=self.hit_count,
            miss_count=self.miss_count + 1,
        )

    @property
    def size(self) -> int:
        """获取缓存条目数。

        Get number of cached entries.

        Returns:
            缓存条目数量。
            Number of cache entries.
        """
        return self.cache.size

    @property
    def is_empty(self) -> bool:
        """判断缓存是否为空。

        Check if cache is empty.

        Returns:
            无缓存条目时返回 True。
            True when no cache entries.
        """
        return self.cache.is_empty

    @property
    def total_lookups(self) -> int:
        """获取总查询次数。

        Get total lookup count.

        Returns:
            命中与未命中次数之和。
            Sum of hit and miss counts.
        """
        return self.hit_count + self.miss_count

    @property
    def hit_rate(self) -> float:
        """获取缓存命中率。

        Get cache hit rate.

        Returns:
            命中率（0.0 ~ 1.0），无查询时返回 0.0。
            Hit rate (0.0 ~ 1.0), 0.0 when no lookups.
        """
        total = self.total_lookups
        if total <= 0:
            zero_rate = 0.0
            return zero_rate
        return self.hit_count / total
