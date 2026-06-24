"""CSP1D 余料最小化配置 / CSP1D waste minimization config."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WasteMinimizationConfig:
    """余料最小化配置 / Waste minimization configuration.

    控制余料最小化阶段的行为参数。
    Controls behavior parameters of the waste
    minimization phase.

    Attributes:
        enabled: 是否启用余料最小化 / Whether waste
            minimization is enabled.
        weight: 余料目标权重 / Weight of the waste objective.
        max_iterations: 最大迭代次数 / Maximum iterations.
        tolerance: 收敛容差 / Convergence tolerance.
    """

    enabled: bool = True
    weight: float = 1.0
    max_iterations: int = 100
    tolerance: float = 1e-6
