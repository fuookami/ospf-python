"""不精确聚合 / Imprecise aggregation.

提供层分配的不精确聚合策略。
Provides imprecise aggregation strategy for layer assignment.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImpreciseAggregation:
    """不精确聚合 / Imprecise aggregation.

    允许在聚合过程中存在容差。
    Allows tolerance during the aggregation process.

    Attributes:
        tolerance: 容差值 / The tolerance value.
        max_deviation: 最大偏差 / The maximum deviation.
    """

    tolerance: float = 0.01
    max_deviation: float = 0.05
