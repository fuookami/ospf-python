"""求解器状态枚举 / Solver status enumeration.

定义求解器返回的状态码。
Defines status codes returned by solvers.
"""

from __future__ import annotations

import enum


class SolverStatus(enum.Enum):
    """求解器状态枚举 / Solver status enumeration.

    描述求解器执行完成后的状态。
    Describes the solver state after execution completes.

    Attributes:
        value: 状态整数值 / The integer status value.
    """

    OPTIMAL = 0
    """最优解 / Optimal solution found."""

    INFEASIBLE = 1
    """不可行 / Problem is infeasible."""

    UNBOUNDED = 2
    """无界 / Problem is unbounded."""

    TIMEOUT = 3
    """超时 / Time limit reached."""

    ERROR = 4
    """错误 / Solver encountered an error."""

    UNKNOWN = 5
    """未知 / Unknown status."""
