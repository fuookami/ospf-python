"""模拟求解器 / Mock solver.

用于测试的内存求解器，能处理简单 LP/MILP 问题。
In-memory solver for testing that handles simple LP/MILP
problems.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.core.model.intermediate.linear_triad_model import (
    LinearTriadModel,
)
from ospf_python.core.solver.linear_solver import (
    LinearSolver,
)
from ospf_python.core.solver.output.solver_output import (
    SolverOutput,
)
from ospf_python.core.solver.output.solver_status import (
    SolverStatus,
)
from ospf_python.core.solver.value.solve_value import (
    SolveValue,
)

if TYPE_CHECKING:
    from ospf_python.core.solver.solve_options import (
        SolveOptions,
    )


@dataclass(frozen=True)
class MockSolver(LinearSolver):
    """模拟求解器 / Mock solver.

    冻结数据类，实现 LinearSolver 接口，使用简单逻辑
    求解 LinearTriadModel 中的 LP/MILP 问题。
    Frozen dataclass implementing the LinearSolver interface,
    using simple logic to solve LP/MILP problems from a
    LinearTriadModel.

    Attributes:
        supports_int: 是否支持整数变量 / Whether integer
            variables are supported.
    """

    supports_int: bool = True
    """是否支持整数变量 / Whether integer variables are
    supported."""

    @property
    def name(self) -> str:
        """求解器名称 / Solver name.

        Returns:
            'mock' / 'mock'.
        """
        return "mock"

    def supports_integer(self) -> bool:
        """是否支持整数变量 / Whether integer variables
        are supported.

        Returns:
            支持整数变量时返回 True / True when integer
            variables are supported.
        """
        return self.supports_int

    def solve(
        self,
        model: object,
        *,
        options: SolveOptions | None = None,
    ) -> SolverOutput:
        """求解模型 / Solve the model.

        对 LinearTriadModel 执行简单求解逻辑。
        Executes simple solve logic on a LinearTriadModel.

        Args:
            model: 要求解的模型 / The model to solve.
            options: 求解选项 / Solve options.

        Returns:
            求解输出 / Solver output.
        """
        if not isinstance(model, LinearTriadModel):
            return SolverOutput(
                status=SolverStatus.ERROR,
            )
        return self._solve_triad(model, options)

    def _solve_triad(
        self,
        model: LinearTriadModel,
        options: SolveOptions | None,
    ) -> SolverOutput:
        """求解线性三元组模型 / Solve a linear triad model.

        使用简单逻辑求解：将所有变量设为其下界值，
        如果无下界则设为 0。
        Uses simple logic: sets all variables to their
        lower bound, or 0 if no lower bound.

        Args:
            model: 线性三元组模型 / The linear triad model.
            options: 求解选项 / Solve options.

        Returns:
            求解输出 / Solver output.
        """
        variables = model.variables
        if not variables and model.objective:
            variables = list(model.objective.keys())
        if not variables:
            return SolverOutput(
                status=SolverStatus.INFEASIBLE,
            )

        values: dict[str, float] = {}
        for var in variables:
            lb = model.lower_bounds.get(var, 0.0)
            values[var] = lb

        if not self._check_feasibility(model, values):
            return SolverOutput(
                status=SolverStatus.INFEASIBLE,
            )

        objective = self._compute_objective(
            model,
            values,
        )
        return SolverOutput(
            status=SolverStatus.OPTIMAL,
            objective=objective,
            values=SolveValue(values=values),
        )

    def _check_feasibility(
        self,
        model: LinearTriadModel,
        values: dict[str, float],
    ) -> bool:
        """检查可行性 / Check feasibility.

        验证赋值是否满足所有约束。
        Verifies that the assignment satisfies all
        constraints.

        Args:
            model: 线性三元组模型 / The linear triad model.
            values: 变量赋值 / Variable assignments.

        Returns:
            可行返回 True / True when feasible.
        """
        for cname, coeffs in model.constraints.items():
            lhs = sum(coeffs.get(v, 0.0) * values.get(v, 0.0) for v in coeffs)
            rhs = model.rhs.get(cname, 0.0)
            sense = model.sense.get(cname, "<=")
            if sense == "<=" and lhs > rhs + 1e-8:
                return False
            if sense == ">=" and lhs < rhs - 1e-8:
                return False
            if sense == "==" and abs(lhs - rhs) > 1e-8:
                return False
        return True

    @staticmethod
    def _compute_objective(
        model: LinearTriadModel,
        values: dict[str, float],
    ) -> float:
        """计算目标函数值 / Compute objective value.

        Args:
            model: 线性三元组模型 / The linear triad model.
            values: 变量赋值 / Variable assignments.

        Returns:
            目标函数值 / Objective value.
        """
        return sum(
            coeff * values.get(var, 0.0) for var, coeff in model.objective.items()
        )
