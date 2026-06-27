"""CSP1D 模板复用管理。

管理切割方案模板的跨材料复用。
Manages reuse of cutting plan templates across materials.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationTemplateReuse:
    """模板复用管理 / Template reuse manager.

    跟踪已使用的切割方案模板及其来源材料，
    支持将模板从一种材料复用到宽度兼容的其他材料。
    Tracks used cutting plan templates and their source
    materials, supporting template reuse across materials
    with compatible widths.

    Attributes:
        reuse_map: 源材料到目标材料列表的映射。
            Source material to target materials mapping.
        registered_templates: 已注册的模板列表。
            List of registered templates.
    """

    reuse_map: tuple[tuple[str, tuple[str, ...]], ...] = ()
    """源材料到目标材料的映射 / Source to target materials mapping."""

    registered_templates: tuple[tuple[str, dict[str, int]], ...] = ()
    """已注册模板 / Registered templates (material, plan)."""

    def register(
        self,
        source_material: str,
        template: dict[str, int],
    ) -> GenerationTemplateReuse:
        """注册模板及其来源材料。

        Register template with its source material.

        Args:
            source_material: 来源材料名称。
                Source material name.
            template: 切割方案模板。
                Cutting plan template.

        Returns:
            更新后的复用管理实例。
            Updated reuse manager instance.
        """
        new_templates = self.registered_templates + (
            (source_material, template),
        )
        return GenerationTemplateReuse(
            reuse_map=self.reuse_map,
            registered_templates=new_templates,
        )

    def add_reuse_link(
        self,
        source_material: str,
        target_material: str,
    ) -> GenerationTemplateReuse:
        """添加材料间的复用链接。

        Add reuse link between materials.

        Args:
            source_material: 源材料名称。
                Source material name.
            target_material: 目标材料名称。
                Target material name.

        Returns:
            更新后的复用管理实例。
            Updated reuse manager instance.
        """
        existing_targets: list[str] = []
        for src, targets in self.reuse_map:
            if src == source_material:
                existing_targets = list(targets)
                break
        if target_material not in existing_targets:
            existing_targets.append(target_material)
        new_reuse_map = tuple(
            (src, tgts)
            for src, tgts in self.reuse_map
            if src != source_material
        ) + ((source_material, tuple(existing_targets)),)
        return GenerationTemplateReuse(
            reuse_map=new_reuse_map,
            registered_templates=self.registered_templates,
        )

    def get_targets(
        self,
        source_material: str,
    ) -> tuple[str, ...]:
        """获取可复用的目标材料列表。

        Get list of target materials for reuse.

        Args:
            source_material: 源材料名称。
                Source material name.

        Returns:
            目标材料元组，不存在返回空元组。
            Tuple of target materials, empty if not found.
        """
        for src, targets in self.reuse_map:
            if src == source_material:
                return targets
        return ()

    def get_templates_for(
        self,
        material: str,
    ) -> tuple[dict[str, int], ...]:
        """获取指定材料的已注册模板。

        Get registered templates for the specified material.

        Args:
            material: 材料名称。
                Material name.

        Returns:
            模板元组。
            Tuple of templates.
        """
        return tuple(
            tpl for src, tpl in self.registered_templates if src == material
        )

    def can_reuse(
        self,
        source_material: str,
        target_material: str,
    ) -> bool:
        """检查是否可以复用模板。

        Check if template can be reused.

        Args:
            source_material: 源材料名称。
                Source material name.
            target_material: 目标材料名称。
                Target material name.

        Returns:
            可以复用返回 True / True if reusable.
        """
        targets = self.get_targets(source_material)
        return target_material in targets

    @property
    def total_registered(self) -> int:
        """获取已注册模板总数。

        Get total number of registered templates.

        Returns:
            模板总数。
            Total number of templates.
        """
        return len(self.registered_templates)

    @property
    def reuse_link_count(self) -> int:
        """获取复用链接总数。

        Get total number of reuse links.

        Returns:
            链接总数。
            Total number of links.
        """
        return sum(len(targets) for _, targets in self.reuse_map)
