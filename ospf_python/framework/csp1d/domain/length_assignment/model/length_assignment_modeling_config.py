"""CSP1D 长度分配建模配置。

配置长度分配优化模型的参数。
Configuration for length assignment optimization modeling.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LengthAssignmentModelingConfig:
    """长度分配建模配置 / Length assignment modeling config.

    控制长度分配 MILP 模型的求解行为。
    Controls solving behavior of the length
    assignment MILP model.

    Attributes:
        min_length: 允许的最小长度。
            Minimum allowed length.
        max_length: 允许的最大长度。
            Maximum allowed length.
        length_step: 长度离散步长。
            Length discretization step.
        allow_shortfall: 是否允许缺口。
            Whether shortfall is allowed.
        shortfall_penalty: 缺口惩罚系数。
            Shortfall penalty coefficient.
        waste_penalty: 余料惩罚系数。
            Waste penalty coefficient.
        precision: 数值精度。
            Numerical precision.
    """

    min_length: float = 0.0
    """最小长度 / Minimum length."""

    max_length: float = float("inf")
    """最大长度 / Maximum length."""

    length_step: float = 1.0
    """长度步长 / Length step."""

    allow_shortfall: bool = False
    """是否允许缺口 / Allow shortfall."""

    shortfall_penalty: float = 1000.0
    """缺口惩罚 / Shortfall penalty."""

    waste_penalty: float = 1.0
    """余料惩罚 / Waste penalty."""

    precision: float = 1e-8
    """数值精度 / Numerical precision."""

    @staticmethod
    def default() -> LengthAssignmentModelingConfig:
        """创建默认配置。

        Create default configuration.

        Returns:
            默认配置实例。
            Default config instance.
        """
        return LengthAssignmentModelingConfig()

    @staticmethod
    def with_length_range(
        *,
        min_length: float,
        max_length: float,
    ) -> LengthAssignmentModelingConfig:
        """创建指定长度范围的配置。

        Create config with specified length range.

        Args:
            min_length: 最小长度。
                Minimum length.
            max_length: 最大长度。
                Maximum length.

        Returns:
            配置实例。
            Config instance.
        """
        return LengthAssignmentModelingConfig(
            min_length=min_length,
            max_length=max_length,
        )
