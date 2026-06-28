"""CSP1D 材料聚合。

聚合材料领域的多个模型组件。
Aggregation for CSP1D material domain.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.csp1d.domain.material.model.machine import Machine
    from ospf_python.framework.csp1d.domain.material.model.material import Material
    from ospf_python.framework.csp1d.domain.material.model.product import Product


@dataclass(frozen=True)
class Aggregation:
    """材料域聚合 / Material domain aggregation.

    聚合原材料、产品和机器定义，提供统一的
    领域数据访问入口。
    Aggregates raw materials, products, and machine
    definitions, providing a unified domain data
    access entry point.

    Attributes:
        materials: 原材料列表。
            Raw materials.
        products: 产品列表。
            Products.
        machines: 机器列表。
            Machines.
    """

    materials: tuple[Material, ...] = ()
    """原材料列表 / Raw materials."""

    products: tuple[Product, ...] = ()
    """产品列表 / Products."""

    machines: tuple[Machine, ...] = ()
    """机器列表 / Machines."""

    @staticmethod
    def create(
        *,
        materials: tuple[Material, ...] = (),
        products: tuple[Product, ...] = (),
        machines: tuple[Machine, ...] = (),
    ) -> Aggregation:
        """创建材料聚合。

        Create material aggregation.

        Args:
            materials: 原材料列表。
                Raw materials.
            products: 产品列表。
                Products.
            machines: 机器列表。
                Machines.

        Returns:
            聚合实例。
            Aggregation instance.
        """
        return Aggregation(
            materials=materials,
            products=products,
            machines=machines,
        )

    def with_materials(
        self,
        *,
        materials: tuple[Material, ...],
    ) -> Aggregation:
        """创建包含新材料的新聚合。

        Create new aggregation with materials.

        Args:
            materials: 原材料列表。
                Raw materials.

        Returns:
            新聚合实例。
            New aggregation instance.
        """
        return Aggregation(
            materials=materials,
            products=self.products,
            machines=self.machines,
        )

    def with_products(
        self,
        *,
        products: tuple[Product, ...],
    ) -> Aggregation:
        """创建包含新产品的新聚合。

        Create new aggregation with products.

        Args:
            products: 产品列表。
                Products.

        Returns:
            新聚合实例。
            New aggregation instance.
        """
        return Aggregation(
            materials=self.materials,
            products=products,
            machines=self.machines,
        )

    def with_machines(
        self,
        *,
        machines: tuple[Machine, ...],
    ) -> Aggregation:
        """创建包含新机器的新聚合。

        Create new aggregation with machines.

        Args:
            machines: 机器列表。
                Machines.

        Returns:
            新聚合实例。
            New aggregation instance.
        """
        return Aggregation(
            materials=self.materials,
            products=self.products,
            machines=machines,
        )

    def get_material(self, name: str) -> Material | None:
        """按名称获取原材料。

        Get raw material by name.

        Args:
            name: 材料名称。
                Material name.

        Returns:
            材料实例，不存在返回 None。
            Material instance, None if not found.
        """
        return next(
            (mat for mat in self.materials if mat.name == name),
            None,
        )

    def get_product(self, name: str) -> Product | None:
        """按名称获取产品。

        Get product by name.

        Args:
            name: 产品名称。
                Product name.

        Returns:
            产品实例，不存在返回 None。
            Product instance, None if not found.
        """
        return next(
            (prod for prod in self.products if prod.name == name),
            None,
        )

    def get_machine(self, name: str) -> Machine | None:
        """按名称获取机器。

        Get machine by name.

        Args:
            name: 机器名称。
                Machine name.

        Returns:
            机器实例，不存在返回 None。
            Machine instance, None if not found.
        """
        return next(
            (mch for mch in self.machines if mch.name == name),
            None,
        )

    @property
    def material_count(self) -> int:
        """获取原材料种类数。

        Get number of material types.

        Returns:
            原材料种类数量。
            Number of material types.
        """
        return len(self.materials)

    @property
    def product_count(self) -> int:
        """获取产品种类数。

        Get number of product types.

        Returns:
            产品种类数量。
            Number of product types.
        """
        return len(self.products)

    @property
    def machine_count(self) -> int:
        """获取机器种类数。

        Get number of machine types.

        Returns:
            机器种类数量。
            Number of machine types.
        """
        return len(self.machines)

    @property
    def total_demand(self) -> int:
        """获取总产品需求量。

        Get total product demand.

        Returns:
            所产品需求量之和。
            Sum of all product demands.
        """
        return sum(p.demand for p in self.products)

    @property
    def is_empty(self) -> bool:
        """判断聚合是否为空。

        Check if aggregation is empty.

        Returns:
            无材料、产品和机器时返回 True。
            True when no materials, products, or machines.
        """
        return (
            len(self.materials) == 0
            and len(self.products) == 0
            and len(self.machines) == 0
        )
