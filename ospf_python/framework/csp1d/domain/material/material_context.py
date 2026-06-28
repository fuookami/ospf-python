"""CSP1D 材料上下文。

管理 CSP1D 材料域的注册表和查询。
Registry for the CSP1D material domain.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.csp1d.domain.material.model.machine import Machine
    from ospf_python.framework.csp1d.domain.material.model.material import Material
    from ospf_python.framework.csp1d.domain.material.model.product import Product


@dataclass(frozen=True)
class MaterialContext:
    """CSP1D 材料上下文 / CSP1D material context.

    维护原材料、产品和机器的注册表，提供注册、
    查询和管理功能。
    Maintains raw material, product, and machine
    registries, providing registration, query,
    and management functions.

    Attributes:
        materials: 已注册的原材料。
            Registered raw materials.
        products: 已注册的产品。
            Registered products.
        machines: 已注册的机器。
            Registered machines.
        current_material: 当前选中的材料名称。
            Currently selected material name.
    """

    materials: tuple[Material, ...] = ()
    """已注册的原材料 / Registered raw materials."""

    products: tuple[Product, ...] = ()
    """已注册的产品 / Registered products."""

    machines: tuple[Machine, ...] = ()
    """已注册的机器 / Registered machines."""

    current_material: str = ""
    """当前选中的材料名称 / Currently selected material name."""

    def register_material(
        self,
        material: Material,
    ) -> MaterialContext:
        """注册原材料，返回新上下文。

        Register raw material, return new context.

        Args:
            material: 原材料实例。
                Raw material instance.

        Returns:
            包含新材料的上下文实例。
            Context with new material.
        """
        return MaterialContext(
            materials=self.materials + (material,),
            products=self.products,
            machines=self.machines,
            current_material=self.current_material,
        )

    def register_product(
        self,
        product: Product,
    ) -> MaterialContext:
        """注册产品，返回新上下文。

        Register product, return new context.

        Args:
            product: 产品实例。
                Product instance.

        Returns:
            包含新产品的上下文实例。
            Context with new product.
        """
        return MaterialContext(
            materials=self.materials,
            products=self.products + (product,),
            machines=self.machines,
            current_material=self.current_material,
        )

    def register_machine(
        self,
        machine: Machine,
    ) -> MaterialContext:
        """注册机器，返回新上下文。

        Register machine, return new context.

        Args:
            machine: 机器实例。
                Machine instance.

        Returns:
            包含新机器的上下文实例。
            Context with new machine.
        """
        return MaterialContext(
            materials=self.materials,
            products=self.products,
            machines=self.machines + (machine,),
            current_material=self.current_material,
        )

    def select_material(
        self,
        name: str,
    ) -> MaterialContext:
        """选择当前材料，返回新上下文。

        Select current material, return new context.

        Args:
            name: 材料名称。
                Material name.

        Returns:
            更新当前材料的上下文实例。
            Context with updated current material.
        """
        return MaterialContext(
            materials=self.materials,
            products=self.products,
            machines=self.machines,
            current_material=name,
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

    def contains_material(self, name: str) -> bool:
        """检查材料是否已注册。

        Check if material is registered.

        Args:
            name: 材料名称。
                Material name.

        Returns:
            已注册返回 True / True if registered.
        """
        return any(mat.name == name for mat in self.materials)

    def contains_product(self, name: str) -> bool:
        """检查产品是否已注册。

        Check if product is registered.

        Args:
            name: 产品名称。
                Product name.

        Returns:
            已注册返回 True / True if registered.
        """
        return any(prod.name == name for prod in self.products)

    @property
    def material_count(self) -> int:
        """获取已注册材料数量。

        Get number of registered materials.

        Returns:
            材料数量。
            Number of materials.
        """
        return len(self.materials)

    @property
    def product_count(self) -> int:
        """获取已注册产品数量。

        Get number of registered products.

        Returns:
            产品数量。
            Number of products.
        """
        return len(self.products)

    @property
    def machine_count(self) -> int:
        """获取已注册机器数量。

        Get number of registered machines.

        Returns:
            机器数量。
            Number of machines.
        """
        return len(self.machines)

    @property
    def is_empty(self) -> bool:
        """判断上下文是否为空。

        Check if context is empty.

        Returns:
            无任何注册项时返回 True。
            True when no registrations.
        """
        return (
            len(self.materials) == 0
            and len(self.products) == 0
            and len(self.machines) == 0
        )
