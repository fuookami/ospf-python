"""CSP1D 长度分配聚合。

聚合长度分配领域的多个模型组件。
Aggregation for length assignment domain.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.framework.csp1d.domain.length_assignment.model.length_assignment_model import (
    LengthAssignmentModel,
)
from ospf_python.framework.csp1d.domain.length_assignment.model.length_assignment_modeling_config import (
    LengthAssignmentModelingConfig,
)


@dataclass(frozen=True)
class LengthAggregation:
    """长度分配聚合 / Length assignment aggregation.

    聚合长度分配模型及其配置，协调注册顺序。
    Aggregates length assignment model and config,
    coordinating registration order.

    Attributes:
        model: 长度分配模型。
            Length assignment model.
        config: 建模配置。
            Modeling config.
        shadow_prices: 影子价格映射。
            Shadow price mapping.
    """

    model: LengthAssignmentModel = field(
        default_factory=LengthAssignmentModel,
    )
    """长度分配模型 / Length assignment model."""

    config: LengthAssignmentModelingConfig = field(
        default_factory=LengthAssignmentModelingConfig,
    )
    """建模配置 / Modeling config."""

    shadow_prices: tuple[tuple[str, float], ...] = ()
    """影子价格映射 / Shadow price mapping."""

    @staticmethod
    def create(
        *,
        config: LengthAssignmentModelingConfig,
        material_lengths: tuple[float, ...],
        product_lengths: tuple[float, ...],
    ) -> LengthAggregation:
        """创建长度分配聚合。

        Create length assignment aggregation.

        Args:
            config: 建模配置。
                Modeling config.
            material_lengths: 可用材料长度。
                Available material lengths.
            product_lengths: 产品需求长度。
                Product demand lengths.

        Returns:
            聚合实例。
            Aggregation instance.
        """
        model = LengthAssignmentModel.create(
            config=config,
            material_lengths=material_lengths,
            product_lengths=product_lengths,
        )
        return LengthAggregation(model=model, config=config)

    def with_shadow_prices(
        self,
        *,
        prices: dict[str, float],
    ) -> LengthAggregation:
        """创建包含影子价格的新聚合。

        Create new aggregation with shadow prices.

        Args:
            prices: 产品键到影子价格的映射。
                Product key to shadow price mapping.

        Returns:
            新聚合实例。
            New aggregation instance.
        """
        items = tuple(sorted(prices.items(), key=lambda kv: kv[0]))
        return LengthAggregation(
            model=self.model,
            config=self.config,
            shadow_prices=items,
        )

    def get_shadow_price(self, product_key: str) -> float:
        """获取指定产品的影子价格。

        Get shadow price for the specified product.

        Args:
            product_key: 产品键。
                Product key.

        Returns:
            影子价格，不存在返回 0.0。
            Shadow price, 0.0 if not found.
        """
        for k, p in self.shadow_prices:
            if k == product_key:
                return p
        return 0.0
