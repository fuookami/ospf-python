"""CSP1D 切片模板缓存。

缓存切片模板以供跨材料复用。
Caches slice templates for reuse across materials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.cutting_plan_canonical_key import (
        CuttingPlanCanonicalKey,
    )


@dataclass(frozen=True)
class GenerationSliceTemplateCache:
    """切片模板缓存 / Slice template cache.

    以规范键为索引缓存切片模板，
    避免为相同产品组合重复生成模板。
    Caches slice templates indexed by canonical key,
    avoiding redundant template generation for identical
    product combinations.

    Attributes:
        templates: 规范键到切片模板的映射。
            Canonical key to slice template mapping.
    """

    templates: tuple[tuple[CuttingPlanCanonicalKey, dict[str, int]], ...] = ()
    """规范键到切片模板的映射 / Canonical key to template mapping."""

    def get(
        self,
        key: CuttingPlanCanonicalKey,
    ) -> dict[str, int] | None:
        """获取指定键的切片模板。

        Get slice template for the specified key.

        Args:
            key: 规范键。
                Canonical key.

        Returns:
            切片模板，不存在返回 None。
            Slice template, None if not found.
        """
        return next(
            (template for cached_key, template in self.templates if cached_key == key),
            None,
        )

    def put(
        self,
        key: CuttingPlanCanonicalKey,
        template: dict[str, int],
    ) -> GenerationSliceTemplateCache:
        """添加切片模板。

        Add slice template.

        Args:
            key: 规范键。
                Canonical key.
            template: 切片模板。
                Slice template.

        Returns:
            包含新模板的缓存实例。
            Cache instance with new template.
        """
        new_templates = self.templates + ((key, template),)
        return GenerationSliceTemplateCache(templates=new_templates)

    def contains(self, key: CuttingPlanCanonicalKey) -> bool:
        """检查是否包含指定键。

        Check if cache contains the specified key.

        Args:
            key: 规范键。
                Canonical key.

        Returns:
            包含返回 True / True if contained.
        """
        return any(cached_key == key for cached_key, _ in self.templates)

    @property
    def size(self) -> int:
        """获取缓存模板数量。

        Get number of cached templates.

        Returns:
            模板数量。
            Number of templates.
        """
        return len(self.templates)

    @property
    def is_empty(self) -> bool:
        """判断缓存是否为空。

        Check if cache is empty.

        Returns:
            无模板时返回 True。
            True when no templates.
        """
        return len(self.templates) == 0

    def all_templates(self) -> tuple[dict[str, int], ...]:
        """获取所有缓存的切片模板。

        Get all cached slice templates.

        Returns:
            切片模板元组。
            Tuple of slice templates.
        """
        return tuple(tpl for _, tpl in self.templates)
