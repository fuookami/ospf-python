"""CSP1D 生产数据。

描述单条生产记录。
Production data for a single production record.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Produce:
    """生产数据 / Production data.

    描述一条生产记录，关联产品、材料和机器。
    Describes a production record linking product,
    material, and machine.

    Attributes:
        product_key: 产品标识 / Product identifier.
        material_key: 材料标识 / Material identifier.
        machine_key: 机器标识 / Machine identifier.
        quantity: 生产数量 / Production quantity.
        length: 使用长度 / Used length.
        cutting_plan_key: 切割方案标识。
            Cutting plan identifier.
    """

    product_key: str = ""
    """产品标识 / Product identifier."""

    material_key: str = ""
    """材料标识 / Material identifier."""

    machine_key: str = ""
    """机器标识 / Machine identifier."""

    quantity: int = 0
    """生产数量 / Production quantity."""

    length: float = 0.0
    """使用长度 / Used length."""

    cutting_plan_key: str = ""
    """切割方案标识 / Cutting plan identifier."""

    @staticmethod
    def create(
        *,
        product_key: str,
        material_key: str,
        machine_key: str,
        quantity: int = 0,
        length: float = 0.0,
        cutting_plan_key: str = "",
    ) -> Produce:
        """创建生产数据。

        Create production data.

        Args:
            product_key: 产品标识。
                Product identifier.
            material_key: 材料标识。
                Material identifier.
            machine_key: 机器标识。
                Machine identifier.
            quantity: 生产数量，默认 0。
                Production quantity, default 0.
            length: 使用长度，默认 0.0。
                Used length, default 0.0.
            cutting_plan_key: 切割方案标识，默认空。
                Cutting plan identifier, default empty.

        Returns:
            生产数据实例。
            Production data instance.
        """
        return Produce(
            product_key=product_key,
            material_key=material_key,
            machine_key=machine_key,
            quantity=quantity,
            length=length,
            cutting_plan_key=cutting_plan_key,
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

    def with_quantity(self, quantity: int) -> Produce:
        """创建更新数量的新实例。

        Create new instance with updated quantity.

        Args:
            quantity: 新的生产数量。
                New production quantity.

        Returns:
            新的生产数据实例。
            New production data instance.
        """
        return Produce(
            product_key=self.product_key,
            material_key=self.material_key,
            machine_key=self.machine_key,
            quantity=quantity,
            length=self.length,
            cutting_plan_key=self.cutting_plan_key,
        )
