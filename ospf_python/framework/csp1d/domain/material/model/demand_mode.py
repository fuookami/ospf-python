"""CSP1D 需求模式枚举 / CSP1D demand mode enum."""

from __future__ import annotations

import enum


class DemandMode(enum.Enum):
    """需求满足模式 / Demand satisfaction mode.

    定义产品需求量的约束方式。
    Defines how product demand quantities are constrained.

    Attributes:
        EXACT: 精确满足需求 / Demand must be met exactly.
        AT_LEAST: 至少满足需求 / Demand must be met at least.
        AT_MOST: 至多满足需求 / Demand must be met at most.
    """

    EXACT = "exact"
    AT_LEAST = "at_least"
    AT_MOST = "at_most"
