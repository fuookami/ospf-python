"""CSP1D 渲染 DTO。

用于将 CSP1D 解决方案渲染为可展示格式。
Render DTO for presenting CSP1D solutions.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RenderDto:
    """渲染 DTO / Render DTO.

    将 CSP1D 解决方案转换为前端可展示的格式，
    包括切割方案详情、材料使用和统计信息。
    Converts CSP1D solutions to frontend-presentable
    format, including cutting plan details,
    material usage, and statistics.

    Attributes:
        plan_id: 方案标识 / Plan identifier.
        material_key: 材料标识 / Material identifier.
        material_length: 材料长度 / Material length.
        products: 产品列表，每项为
            (产品键, 宽度, 数量)。
            Product list, each item is
            (product_key, width, quantity).
        used_length: 已使用长度 / Used length.
        waste_length: 余料长度 / Waste length.
        machine_key: 机器标识 / Machine identifier.
        batch_index: 批次序号 / Batch index.
    """

    plan_id: str = ""
    """方案标识 / Plan identifier."""

    material_key: str = ""
    """材料标识 / Material identifier."""

    material_length: float = 0.0
    """材料长度 / Material length."""

    products: tuple[tuple[str, float, int], ...] = ()
    """产品列表 / Product list."""

    used_length: float = 0.0
    """已使用长度 / Used length."""

    waste_length: float = 0.0
    """余料长度 / Waste length."""

    machine_key: str = ""
    """机器标识 / Machine identifier."""

    batch_index: int = 0
    """批次序号 / Batch index."""

    @staticmethod
    def create(
        *,
        plan_id: str,
        material_key: str,
        material_length: float,
        products: tuple[tuple[str, float, int], ...],
        machine_key: str = "",
        batch_index: int = 0,
    ) -> RenderDto:
        """创建渲染 DTO。

        Create render DTO.

        Args:
            plan_id: 方案标识。
                Plan identifier.
            material_key: 材料标识。
                Material identifier.
            material_length: 材料长度。
                Material length.
            products: 产品列表。
                Product list.
            machine_key: 机器标识，默认空。
                Machine key, default empty.
            batch_index: 批次序号，默认 0。
                Batch index, default 0.

        Returns:
            渲染 DTO 实例。
            Render DTO instance.
        """
        used = sum(w * q for _, w, q in products)
        waste = max(0.0, material_length - used)
        return RenderDto(
            plan_id=plan_id,
            material_key=material_key,
            material_length=material_length,
            products=products,
            used_length=used,
            waste_length=waste,
            machine_key=machine_key,
            batch_index=batch_index,
        )

    @property
    def utilization_ratio(self) -> float:
        """获取利用率。

        Get utilization ratio.

        Returns:
            利用率（0.0 ~ 1.0）。
            Utilization ratio (0.0 ~ 1.0).
        """
        if self.material_length <= 1e-8:
            return 0.0
        return self.used_length / self.material_length

    @property
    def product_count(self) -> int:
        """获取产品种类数。

        Get number of product types.

        Returns:
            产品种类数。
            Number of product types.
        """
        return len(self.products)

    @property
    def total_cuts(self) -> int:
        """获取总切割数。

        Get total cuts.

        Returns:
            所有产品数量之和。
            Sum of all product quantities.
        """
        return sum(q for _, _, q in self.products)

    def to_dict(self) -> dict[str, object]:
        """转换为字典。

        Convert to dictionary.

        Returns:
            字典表示。
            Dictionary representation.
        """
        return {
            "plan_id": self.plan_id,
            "material_key": self.material_key,
            "material_length": self.material_length,
            "products": [
                {"key": k, "width": w, "quantity": q} for k, w, q in self.products
            ],
            "used_length": self.used_length,
            "waste_length": self.waste_length,
            "utilization_ratio": self.utilization_ratio,
            "machine_key": self.machine_key,
            "batch_index": self.batch_index,
        }
