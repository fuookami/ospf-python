"""CSP1D 产出率模型。

管理产出率优化模型的变量和约束。
Model for yield optimization.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Any


def _load_yield_modeling_config() -> Any:
    """加载 YieldModelingConfig / Load YieldModelingConfig."""
    mod = importlib.import_module(
        "ospf_python.framework.csp1d.domain.yield.model.yield_modeling_config"
    )
    return mod.YieldModelingConfig


@dataclass(frozen=True)
class YieldModel:
    """产出率模型 / Yield model.

    管理产出率优化问题中的决策变量和约束。
    用于评估和优化切割方案的产出率。
    Manages decision variables and constraints in
    the yield optimization problem. Used to evaluate
    and optimize yield ratio of cutting plans.

    Attributes:
        config: 建模配置。
            Modeling config.
        product_yields: 各产品产出数据。
            Per-product yield data.
        material_inputs: 各材料投入量。
            Per-material input amounts.
    """

    config: object = field(
        default_factory=lambda: _load_yield_modeling_config()(),
    )
    """建模配置 / Modeling config."""

    product_yields: tuple[tuple[str, float, float], ...] = ()
    """产品产出数据，格式 (产品键, 产出量, 投入量)。
    Product yield data, format (key, output, input)."""

    material_inputs: tuple[tuple[str, float], ...] = ()
    """材料投入量 / Material input amounts."""

    @staticmethod
    def create(
        *,
        config: object,
    ) -> YieldModel:
        """创建产出率模型。

        Create yield model.

        Args:
            config: 建模配置。
                Modeling config.

        Returns:
            模型实例。
            Model instance.
        """
        return YieldModel(config=config)

    def with_product_yields(
        self,
        *,
        yields: tuple[tuple[str, float, float], ...],
    ) -> YieldModel:
        """创建包含产出数据的新模型。

        Create new model with yield data.

        Args:
            yields: 产品产出数据。
                Product yield data.

        Returns:
            新模型实例。
            New model instance.
        """
        return YieldModel(
            config=self.config,
            product_yields=yields,
            material_inputs=self.material_inputs,
        )

    def get_yield_ratio(self, product_key: str) -> float:
        """获取指定产品的产出率。

        Get yield ratio for the specified product.

        Args:
            product_key: 产品键。
                Product key.

        Returns:
            产出率（0.0 ~ 1.0），不存在返回 0.0。
            Yield ratio (0.0 ~ 1.0), 0.0 if not found.
        """
        precision = getattr(self.config, "precision", 1e-8)
        for key, output, input_amt in self.product_yields:
            if key == product_key:
                if input_amt <= precision:
                    return 0.0
                return output / input_amt
        return 0.0

    @property
    def overall_yield_ratio(self) -> float:
        """获取总体产出率。

        Get overall yield ratio.

        Returns:
            总体产出率。
            Overall yield ratio.
        """
        precision = getattr(self.config, "precision", 1e-8)
        total_output = sum(o for _, o, _ in self.product_yields)
        total_input = sum(i for _, _, i in self.product_yields)
        if total_input <= precision:
            return 0.0
        return total_output / total_input
