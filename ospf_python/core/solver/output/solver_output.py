"""求解器输出 / Solver output.

封装求解器执行完成后的结果。
Encapsulates solver results after execution completes.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.solver.output.solver_status import (
    SolverStatus,
)
from ospf_python.core.solver.value.solve_value import (
    SolveValue,
)


@dataclass(frozen=True, kw_only=True)
class SolverOutput:
    """求解器输出 / Solver output.

    冻结数据类，包含求解状态、目标值和变量值。
    Frozen dataclass containing solve status, objective
    value, and variable values.

    Attributes:
        status: 求解状态 / The solve status.
        objective: 目标函数值 / Objective function value.
        values: 变量值 / Variable values.
    """

    status: SolverStatus
    """求解状态 / The solve status."""

    objective: float = 0.0
    """目标函数值 / Objective function value."""

    values: SolveValue = SolveValue()
    """变量值 / Variable values."""

    @property
    def is_optimal(self) -> bool:
        """是否找到最优解 / Whether optimal was found.

        Returns:
            最优解时返回 True / True when optimal.
        """
        return self.status is SolverStatus.OPTIMAL

    @property
    def is_infeasible(self) -> bool:
        """是否不可行 / Whether infeasible.

        Returns:
            不可行时返回 True / True when infeasible.
        """
        return self.status is SolverStatus.INFEASIBLE

    @staticmethod
    def optimal(
        objective: float,
        values: SolveValue,
    ) -> SolverOutput:
        """创建最优输出 / Create optimal output.

        Args:
            objective: 目标函数值 / Objective value.
            values: 变量值 / Variable values.

        Returns:
            最优输出实例 / Optimal output instance.
        """
        return SolverOutput(
            status=SolverStatus.OPTIMAL,
            objective=objective,
            values=values,
        )

    @staticmethod
    def infeasible() -> SolverOutput:
        """创建不可行输出 / Create infeasible output.

        Returns:
            不可行输出实例 / Infeasible output instance.
        """
        return SolverOutput(
            status=SolverStatus.INFEASIBLE,
        )

    @staticmethod
    def timeout(
        objective: float = 0.0,
        values: SolveValue | None = None,
    ) -> SolverOutput:
        """创建超时输出 / Create timeout output.

        Args:
            objective: 当前目标值 / Current objective.
            values: 当前变量值 / Current values.

        Returns:
            超时输出实例 / Timeout output instance.
        """
        return SolverOutput(
            status=SolverStatus.TIMEOUT,
            objective=objective,
            values=values or SolveValue(),
        )
