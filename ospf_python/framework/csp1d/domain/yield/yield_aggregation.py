"""CSP1D 产出率聚合。

聚合产出率领域的多个模型组件。
Aggregation for yield domain.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field


def _load_yield_model():  # type: ignore[no-untyped-def]
    """加载 YieldModel / Load YieldModel."""
    mod = importlib.import_module(
        "ospf_python.framework.csp1d.domain.yield.model.yield_model"
    )
    return mod.YieldModel


def _load_yield_modeling_config():  # type: ignore[no-untyped-def]
    """加载 YieldModelingConfig / Load YieldModelingConfig."""
    mod = importlib.import_module(
        "ospf_python.framework.csp1d.domain.yield.model.yield_modeling_config"
    )
    return mod.YieldModelingConfig


@dataclass(frozen=True)
class YieldAggregation:
    """产出率聚合 / Yield aggregation.

    聚合产出率模型及其配置，协调领域内
    组件的注册和交互。
    Aggregates yield model and config, coordinating
    component registration and interaction within
    the yield domain.

    Attributes:
        model: 产出率模型。
            Yield model.
        config: 建模配置。
            Modeling config.
        shadow_prices: 影子价格映射。
            Shadow price mapping.
    """

    model: object = field(
        default_factory=lambda: _load_yield_model()(),
    )
    """产出率模型 / Yield model."""

    config: object = field(
        default_factory=lambda: _load_yield_modeling_config()(),
    )
    """建模配置 / Modeling config."""

    shadow_prices: tuple[tuple[str, float], ...] = ()
    """影子价格映射 / Shadow price mapping."""

    @staticmethod
    def create(
        *,
        config: object,
    ) -> YieldAggregation:
        """创建产出率聚合。

        Create yield aggregation.

        Args:
            config: 建模配置。
                Modeling config.

        Returns:
            聚合实例。
            Aggregation instance.
        """
        yield_model_cls = _load_yield_model()
        model = yield_model_cls.create(config=config)
        return YieldAggregation(model=model, config=config)

    def with_shadow_prices(
        self,
        *,
        prices: dict[str, float],
    ) -> YieldAggregation:
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
        return YieldAggregation(
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

    @property
    def overall_yield_ratio(self) -> float:
        """获取总体产出率。

        Get overall yield ratio.

        Returns:
            总体产出率。
            Overall yield ratio.
        """
        return self.model.overall_yield_ratio
