"""CSP1D 渲染映射器。

将领域对象映射为可展示的渲染格式。
Maps domain objects to presentable render formats.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.csp1d.domain.material.model.cutting_plan import (
        CuttingPlan,
    )
    from ospf_python.framework.csp1d.domain.material.model.material import Material
    from ospf_python.framework.csp1d.domain.material.model.product import Product


@dataclass(frozen=True)
class RenderMappers:
    """渲染映射器 / Render mappers.

    将 CSP1D 领域对象（切割方案、材料、产品等）
    映射为可展示的字典格式，用于前端渲染。
    Maps CSP1D domain objects (cutting plans, materials,
    products, etc.) to presentable dict format for
    frontend rendering.

    Attributes:
        material_labels: 材料名称到显示标签的映射。
            Material name to display label mapping.
        product_labels: 产品名称到显示标签的映射。
            Product name to display label mapping.
        precision: 浮点数显示精度。
            Float display precision.
    """

    material_labels: tuple[tuple[str, str], ...] = ()
    """材料标签映射 / Material label mapping."""

    product_labels: tuple[tuple[str, str], ...] = ()
    """产品标签映射 / Product label mapping."""

    precision: int = 2
    """浮点数显示精度 / Float display precision."""

    def map_material(self, material: Material) -> dict[str, object]:
        """将材料映射为字典。

        Map material to dictionary.

        Args:
            material: 材料实例。
                Material instance.

        Returns:
            材料的字典表示。
            Dictionary representation of material.
        """
        label = self.get_material_label(material.name)
        return {
            "name": material.name,
            "label": label,
            "width": round(material.width, self.precision),
            "length": round(material.length, self.precision),
            "cost": round(material.cost, self.precision),
        }

    def map_product(self, product: Product) -> dict[str, object]:
        """将产品映射为字典。

        Map product to dictionary.

        Args:
            product: 产品实例。
                Product instance.

        Returns:
            产品的字典表示。
            Dictionary representation of product.
        """
        label = self.get_product_label(product.name)
        return {
            "name": product.name,
            "label": label,
            "width": round(product.width, self.precision),
            "length": round(product.length, self.precision),
            "demand": product.demand,
        }

    def map_cutting_plan(self, plan: CuttingPlan) -> dict[str, object]:
        """将切割方案映射为字典。

        Map cutting plan to dictionary.

        Args:
            plan: 切割方案实例。
                Cutting plan instance.

        Returns:
            切割方案的字典表示。
            Dictionary representation of cutting plan.
        """
        products = []
        for prod, qty in plan.products:
            products.append({
                "name": prod.name,
                "label": self.get_product_label(prod.name),
                "width": round(prod.width, self.precision),
                "quantity": qty,
            })
        return {
            "material": plan.material,
            "material_label": self.get_material_label(plan.material),
            "products": products,
            "waste": round(plan.waste, self.precision),
        }

    def get_material_label(self, name: str) -> str:
        """获取材料显示标签。

        Get material display label.

        Args:
            name: 材料名称。
                Material name.

        Returns:
            显示标签，无自定义标签时返回原名称。
            Display label, original name if no custom label.
        """
        for mat_name, label in self.material_labels:
            if mat_name == name:
                return label
        return name

    def get_product_label(self, name: str) -> str:
        """获取产品显示标签。

        Get product display label.

        Args:
            name: 产品名称。
                Product name.

        Returns:
            显示标签，无自定义标签时返回原名称。
            Display label, original name if no custom label.
        """
        for prod_name, label in self.product_labels:
            if prod_name == name:
                return label
        return name

    def with_material_labels(
        self,
        *,
        labels: tuple[tuple[str, str], ...],
    ) -> RenderMappers:
        """创建包含新材料标签的新实例。

        Create new instance with material labels.

        Args:
            labels: (名称, 标签) 元组。
                (name, label) tuples.

        Returns:
            新渲染映射器实例。
            New render mapper instance.
        """
        return RenderMappers(
            material_labels=labels,
            product_labels=self.product_labels,
            precision=self.precision,
        )

    def with_product_labels(
        self,
        *,
        labels: tuple[tuple[str, str], ...],
    ) -> RenderMappers:
        """创建包含新产品标签的新实例。

        Create new instance with product labels.

        Args:
            labels: (名称, 标签) 元组。
                (name, label) tuples.

        Returns:
            新渲染映射器实例。
            New render mapper instance.
        """
        return RenderMappers(
            material_labels=self.material_labels,
            product_labels=labels,
            precision=self.precision,
        )

    def with_precision(
        self,
        *,
        precision: int,
    ) -> RenderMappers:
        """创建包含新精度的新实例。

        Create new instance with updated precision.

        Args:
            precision: 浮点数显示精度。
                Float display precision.

        Returns:
            新渲染映射器实例。
            New render mapper instance.
        """
        return RenderMappers(
            material_labels=self.material_labels,
            product_labels=self.product_labels,
            precision=precision,
        )
