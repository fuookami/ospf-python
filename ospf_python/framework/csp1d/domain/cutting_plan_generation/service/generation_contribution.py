"""CSP1D 切割方案贡献。

记录切割方案对各产品的贡献量。
Contribution of a cutting plan to product demands.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationContribution:
    """切割方案贡献 / Cutting plan contribution.

    记录一条切割方案对各产品需求的贡献量，
    用于评估方案的利用率和还原成本。
    Records how a cutting plan contributes to each
    product demand, used to evaluate utilization
    and recovery cost.

    Attributes:
        product_contributions: 产品键到贡献量的映射。
            Product key to contribution quantity mapping.
        total_cuts: 总切割数。
            Total number of cuts.
        waste_length: 余料长度。
            Waste length.
    """

    product_contributions: tuple[tuple[str, int], ...] = ()
    """产品键到贡献量的映射 / Product-contributions mapping."""

    total_cuts: int = 0
    """总切割数 / Total number of cuts."""

    waste_length: float = 0.0
    """余料长度 / Waste length."""

    @staticmethod
    def create(
        *,
        contributions: dict[str, int],
        waste_length: float = 0.0,
    ) -> GenerationContribution:
        """创建贡献实例。

        Create contribution instance.

        Args:
            contributions: 产品键到贡献量的映射。
                Product key to contribution mapping.
            waste_length: 余料长度，默认 0.0。
                Waste length, default 0.0.

        Returns:
            贡献实例。
            Contribution instance.
        """
        items = tuple(sorted(contributions.items(), key=lambda kv: kv[0]))
        total = sum(contributions.values())
        return GenerationContribution(
            product_contributions=items,
            total_cuts=total,
            waste_length=waste_length,
        )

    def contribution_of(self, product_key: str) -> int:
        """获取指定产品的贡献量。

        Get contribution for the specified product.

        Args:
            product_key: 产品键 / Product key.

        Returns:
            贡献量，不存在返回 0。
            Contribution quantity, 0 if not found.
        """
        for k, q in self.product_contributions:
            if k == product_key:
                return q
        return 0

    @property
    def has_waste(self) -> bool:
        """判断是否有余料。

        Check if there is waste.

        Returns:
            余料长度大于精度阈值时返回 True。
            True when waste length exceeds precision.
        """
        return self.waste_length > 1e-8

    @property
    def is_empty(self) -> bool:
        """判断贡献是否为空。

        Check if contribution is empty.

        Returns:
            无任何产品贡献时返回 True。
            True when no product contributions.
        """
        return self.total_cuts == 0
