"""CSP1D 最终 MILP 求解状态 / CSP1D final MILP status."""

from __future__ import annotations

import enum


class Csp1dFinalMilpStatus(enum.Enum):
    """最终 MILP 求解状态 / Final MILP solving status.

    标识列生成结束后最终 MILP 阶段的求解结果。
    Indicates the solving result of the final MILP phase
    after column generation completes.

    Attributes:
        OPTIMAL: 找到最优解 / Optimal solution found.
        INFEASIBLE: 问题不可行 / Problem is infeasible.
        TIMEOUT: 求解超时 / Solving timed out.
    """

    OPTIMAL = "optimal"
    INFEASIBLE = "infeasible"
    TIMEOUT = "timeout"
