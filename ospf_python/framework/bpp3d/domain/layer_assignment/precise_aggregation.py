"""精确聚合 / Precise aggregation.

提供层分配的精确聚合策略。
Provides precise aggregation strategy for layer assignment.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PreciseAggregation:
    """精确聚合 / Precise aggregation.

    在聚合过程中不允许容差。
    Does not allow tolerance during the aggregation process.

    Attributes:
        precision: 精度要求 / The precision requirement.
    """

    precision: float = 1e-10
