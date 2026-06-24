"""CSP1D 长度剪枝。

根据长度限制对搜索空间进行剪枝。
Length-based pruning for cutting plan generation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationLengthPruning:
    """长度剪枝 / Length pruning.

    在生成过程中根据剩余材料长度和产品长度
    决定是否继续搜索或剪枝。
    During generation, decides whether to continue
    searching or prune based on remaining material
    length and product length.

    Attributes:
        material_length: 原材料总长度。
            Total material length.
        min_waste_length: 最小可接受余料长度。
            Minimum acceptable waste length.
        precision: 数值比较精度。
            Numerical comparison precision.
    """

    material_length: float = 0.0
    """原材料总长度 / Total material length."""

    min_waste_length: float = 0.0
    """最小可接受余料长度 / Minimum waste length."""

    precision: float = 1e-8
    """数值精度 / Numerical precision."""

    def should_prune(
        self,
        remaining_length: float,
    ) -> bool:
        """判断是否应剪枝。

        Determine whether to prune.

        Args:
            remaining_length: 当前剩余长度。
                Current remaining length.

        Returns:
            剩余长度不足时返回 True。
            True when remaining length is insufficient.
        """
        return remaining_length < self.min_waste_length - self.precision

    def can_fit_product(
        self,
        remaining_length: float,
        product_length: float,
    ) -> bool:
        """判断剩余空间能否容纳指定产品。

        Check if remaining space can fit the product.

        Args:
            remaining_length: 剩余长度。
                Remaining length.
            product_length: 产品长度。
                Product length.

        Returns:
            可以容纳返回 True / True if can fit.
        """
        return remaining_length >= product_length - self.precision

    def remaining_after_cut(
        self,
        remaining_length: float,
        cut_length: float,
    ) -> float:
        """计算切割后的剩余长度。

        Calculate remaining length after a cut.

        Args:
            remaining_length: 当前剩余长度。
                Current remaining length.
            cut_length: 切割长度。
                Cut length.

        Returns:
            切割后剩余长度。
            Remaining length after cut.
        """
        return remaining_length - cut_length

    def utilization_ratio(
        self,
        used_length: float,
    ) -> float:
        """计算材料利用率。

        Calculate material utilization ratio.

        Args:
            used_length: 已使用长度。
                Used length.

        Returns:
            利用率（0.0 ~ 1.0）。
            Utilization ratio (0.0 ~ 1.0).
        """
        if self.material_length <= self.precision:
            return 0.0
        return used_length / self.material_length
