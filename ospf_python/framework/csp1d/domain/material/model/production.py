"""CSP1D 生产记录。

描述单条 CSP1D 生产记录。
Production record for CSP1D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Production:
    """CSP1D 生产记录 / CSP1D production record.

    描述一条 CSP1D 生产记录，关联产品、材料、机器
    和切割方案，记录生产数量和长度信息。
    Describes a CSP1D production record linking product,
    material, machine, and cutting plan, recording
    production quantity and length info.

    Attributes:
        product_key: 产品标识。
            Product identifier.
        material_key: 材料标识。
            Material identifier.
        machine_key: 机器标识。
            Machine identifier.
        cutting_plan_key: 切割方案标识。
            Cutting plan identifier.
        quantity: 生产数量。
            Production quantity.
        length: 使用长度。
            Used length.
    """

    product_key: str = ""
    """产品标识 / Product identifier."""

    material_key: str = ""
    """材料标识 / Material identifier."""

    machine_key: str = ""
    """机器标识 / Machine identifier."""

    cutting_plan_key: str = ""
    """切割方案标识 / Cutting plan identifier."""

    quantity: int = 0
    """生产数量 / Production quantity."""

    length: float = 0.0
    """使用长度 / Used length."""

    @staticmethod
    def create(
        *,
        product_key: str,
        material_key: str,
        machine_key: str,
        cutting_plan_key: str = "",
        quantity: int = 0,
        length: float = 0.0,
    ) -> Production:
        """创建生产记录。

        Create production record.

        Args:
            product_key: 产品标识。
                Product identifier.
            material_key: 材料标识。
                Material identifier.
            machine_key: 机器标识。
                Machine identifier.
            cutting_plan_key: 切割方案标识，默认空。
                Cutting plan identifier, default empty.
            quantity: 生产数量，默认 0。
                Production quantity, default 0.
            length: 使用长度，默认 0.0。
                Used length, default 0.0.

        Returns:
            生产记录实例。
            Production record instance.
        """
        return Production(
            product_key=product_key,
            material_key=material_key,
            machine_key=machine_key,
            cutting_plan_key=cutting_plan_key,
            quantity=quantity,
            length=length,
        )

    def with_quantity(self, quantity: int) -> Production:
        """创建更新数量的新实例。

        Create new instance with updated quantity.

        Args:
            quantity: 新的生产数量。
                New production quantity.

        Returns:
            新的生产记录实例。
            New production record instance.
        """
        return Production(
            product_key=self.product_key,
            material_key=self.material_key,
            machine_key=self.machine_key,
            cutting_plan_key=self.cutting_plan_key,
            quantity=quantity,
            length=self.length,
        )

    def with_length(self, length: float) -> Production:
        """创建更新长度的新实例。

        Create new instance with updated length.

        Args:
            length: 新的使用长度。
                New used length.

        Returns:
            新的生产记录实例。
            New production record instance.
        """
        return Production(
            product_key=self.product_key,
            material_key=self.material_key,
            machine_key=self.machine_key,
            cutting_plan_key=self.cutting_plan_key,
            quantity=self.quantity,
            length=length,
        )

    @property
    def is_valid(self) -> bool:
        """判断生产记录是否有效。

        Check if production record is valid.

        Returns:
            产品、材料和机器标识非空且数量大于 0 时有效。
            Valid when product, material, machine keys
            are non-empty and quantity > 0.
        """
        return (
            bool(self.product_key)
            and bool(self.material_key)
            and bool(self.machine_key)
            and self.quantity > 0
        )

    @property
    def total_length(self) -> float:
        """获取总使用长度。

        Get total used length.

        Returns:
            使用长度乘以数量。
            Length times quantity.
        """
        return self.length * self.quantity
