"""CSP1D 产出率建模配置。

配置产出率优化模型的参数。
Configuration for yield optimization modeling.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class YieldModelingConfig:
    """产出率建模配置 / Yield modeling config.

    控制产出率优化模型的求解行为和目标权重。
    Controls solving behavior and objective weights
    of the yield optimization model.

    Attributes:
        target_yield_ratio: 目标产出率。
            Target yield ratio.
        yield_weight: 产出率目标权重。
            Yield objective weight.
        min_yield_ratio: 最低可接受产出率。
            Minimum acceptable yield ratio.
        precision: 数值精度。
            Numerical precision.
    """

    target_yield_ratio: float = 0.95
    """目标产出率 / Target yield ratio."""

    yield_weight: float = 1.0
    """产出率权重 / Yield weight."""

    min_yield_ratio: float = 0.0
    """最低产出率 / Min yield ratio."""

    precision: float = 1e-8
    """数值精度 / Numerical precision."""

    @staticmethod
    def default() -> YieldModelingConfig:
        """创建默认配置。

        Create default configuration.

        Returns:
            默认配置实例。
            Default config instance.
        """
        return YieldModelingConfig()

    @staticmethod
    def with_target(
        *,
        target_yield_ratio: float,
    ) -> YieldModelingConfig:
        """创建指定目标的配置。

        Create config with specified target.

        Args:
            target_yield_ratio: 目标产出率。
                Target yield ratio.

        Returns:
            配置实例。
            Config instance.
        """
        return YieldModelingConfig(
            target_yield_ratio=target_yield_ratio,
        )
