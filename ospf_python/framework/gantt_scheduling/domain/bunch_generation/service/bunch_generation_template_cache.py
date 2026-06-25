"""束编组生成模板缓存 / Bunch generation template cache.

缓存已生成的束编组模板以加速重复生成。
Caches generated bunch templates to accelerate repeated
generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.bunch_generation.service.bunch_generator import (
        GeneratedBunch,
    )


@dataclass(frozen=True)
class CacheEntry:
    """缓存条目 / Cache entry.

    Attributes:
        cache_key: 缓存键 / Cache key.
        bunches: 缓存的束编组列表 / Cached bunch list.
        hit_count: 命中次数 / Hit count.
        item_count: 物料项数量 / Item count.
    """

    cache_key: str
    bunches: tuple[GeneratedBunch, ...] = ()
    hit_count: int = 0
    item_count: int = 0


@dataclass(frozen=True)
class CacheStats:
    """缓存统计 / Cache statistics.

    Attributes:
        total_entries: 总条目数 / Total entry count.
        total_hits: 总命中次数 / Total hit count.
        hit_rate: 命中率 / Hit rate.
    """

    total_entries: int = 0
    total_hits: int = 0
    hit_rate: float = 0.0


@dataclass(frozen=True)
class BunchGenerationTemplateCache:
    """束编组生成模板缓存 / Bunch generation template cache.

    缓存已生成的束编组模板，按物料项集合的哈希键索引。
    在重复生成相同或相似分组需求时直接复用缓存结果，
    避免重复计算。
    Caches generated bunch templates, indexed by hash keys of
    material item sets. Directly reuses cached results for
    repeated or similar grouping requirements, avoiding
    redundant computation.

    Attributes:
        entries: 缓存条目列表 / Cache entry list.
        max_size: 最大缓存容量 / Maximum cache capacity.
    """

    entries: tuple[CacheEntry, ...] = ()
    max_size: int = 100

    def get(
        self,
        cache_key: str,
    ) -> tuple[GeneratedBunch, ...] | None:
        """从缓存获取束编组模板。

        Get bunch template from cache.

        Args:
            cache_key: 缓存键。/ Cache key.

        Returns:
            缓存的束编组元组，未命中时返回 None。
            Cached bunch tuple, or None on miss.
        """
        for entry in self.entries:
            if entry.cache_key == cache_key:
                return entry.bunches
        return None

    def put(
        self,
        *,
        cache_key: str,
        bunches: tuple[GeneratedBunch, ...],
        item_count: int,
    ) -> BunchGenerationTemplateCache:
        """添加缓存条目。

        Add a cache entry.

        Args:
            cache_key: 缓存键。/ Cache key.
            bunches: 束编组模板。/ Bunch template.
            item_count: 物料项数量。/ Item count.

        Returns:
            包含新条目的缓存副本。
            A new cache with the entry added.
        """
        new_entry = CacheEntry(
            cache_key=cache_key,
            bunches=bunches,
            hit_count=0,
            item_count=item_count,
        )
        all_entries = self.entries + (new_entry,)
        if len(all_entries) > self.max_size:
            all_entries = all_entries[-self.max_size :]
        return BunchGenerationTemplateCache(
            entries=all_entries,
            max_size=self.max_size,
        )

    def record_hit(
        self,
        cache_key: str,
    ) -> BunchGenerationTemplateCache:
        """记录缓存命中。

        Record a cache hit.

        Args:
            cache_key: 缓存键。/ Cache key.

        Returns:
            命中计数更新后的缓存副本。
            A new cache with hit count updated.
        """
        updated = tuple(
            CacheEntry(
                cache_key=e.cache_key,
                bunches=e.bunches,
                hit_count=e.hit_count + 1 if e.cache_key == cache_key else e.hit_count,
                item_count=e.item_count,
            )
            for e in self.entries
        )
        return BunchGenerationTemplateCache(
            entries=updated,
            max_size=self.max_size,
        )

    def stats(self) -> CacheStats:
        """获取缓存统计 / Get cache statistics.

        Returns:
            缓存统计信息。/ Cache statistics.
        """
        total_hits = sum(e.hit_count for e in self.entries)
        return CacheStats(
            total_entries=len(self.entries),
            total_hits=total_hits,
            hit_rate=(total_hits / max(1, len(self.entries))),
        )

    @staticmethod
    def compute_cache_key(
        item_keys: tuple[str, ...],
    ) -> str:
        """计算缓存键 / Compute cache key.

        Args:
            item_keys: 物料项标识列表。/ Item key list.

        Returns:
            缓存键字符串。/ Cache key string.
        """
        return "|".join(sorted(item_keys))

    def contains(self, cache_key: str) -> bool:
        """检查缓存是否包含指定键。

        Check whether cache contains the key.

        Args:
            cache_key: 缓存键。/ Cache key.

        Returns:
            包含时返回 True。/ True if contains.
        """
        return any(e.cache_key == cache_key for e in self.entries)

    def clear(self) -> BunchGenerationTemplateCache:
        """清空缓存 / Clear cache.

        Returns:
            空缓存副本。/ Empty cache copy.
        """
        return BunchGenerationTemplateCache(
            entries=(),
            max_size=self.max_size,
        )
