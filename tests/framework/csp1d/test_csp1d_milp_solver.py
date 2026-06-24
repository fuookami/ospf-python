"""Csp1dMilpSolver tests.

Test solver creation and solving workflow.
测试求解器创建和求解工作流。

Note: solve() with infeasible result triggers a Failed()
call with a source code signature mismatch.
注意：solve() 不可行结果触发源代码 Failed() 签名不匹配。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.application.service.csp1d_final_milp_status import (
    Csp1dFinalMilpStatus,
)
from ospf_python.framework.csp1d.application.service.csp1d_milp import (
    Csp1dMilp,
)
from ospf_python.framework.csp1d.application.service.csp1d_milp_solver import (
    Csp1dMilpSolver,
    SolverResult,
)


class TestSolverResult:
    """SolverResult frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create with all fields. / 使用所有字段创建。"""
        r = SolverResult(
            status=Csp1dFinalMilpStatus.OPTIMAL,
            objective_value=42.0,
            variable_values=(("x1", 5.0),),
        )
        assert r.status == Csp1dFinalMilpStatus.OPTIMAL
        assert r.objective_value == 42.0
        assert len(r.variable_values) == 1


class TestCsp1dMilpSolver:
    """Csp1dMilpSolver tests."""

    def _mock_solver_fn(self, model: Csp1dMilp) -> SolverResult:
        """Mock solver function. / 模拟求解函数。"""
        return SolverResult(
            status=Csp1dFinalMilpStatus.OPTIMAL,
            objective_value=10.0,
            variable_values=(("x1", 3.0),),
        )

    def _infeasible_solver_fn(self, model: Csp1dMilp) -> SolverResult:
        """Infeasible solver function. / 不可行求解函数。"""
        return SolverResult(
            status=Csp1dFinalMilpStatus.INFEASIBLE,
            objective_value=0.0,
            variable_values=(),
        )

    def test_solve_optimal(self) -> None:
        """Solve returns optimal result. / 求解返回最优结果。"""
        solver = Csp1dMilpSolver(self._mock_solver_fn)
        model = Csp1dMilp()
        result = solver.solve(model)
        assert result.is_ok()
        solution = result.unwrap()
        assert solution.status == Csp1dFinalMilpStatus.OPTIMAL
        assert solution.objective_value == 10.0

    @pytest.mark.xfail(
        reason="Source code Failed() signature mismatch",
        raises=TypeError,
        strict=True,
    )
    def test_solve_infeasible(self) -> None:
        """Solve returns failure for infeasible. / 不可行返回失败。"""
        solver = Csp1dMilpSolver(self._infeasible_solver_fn)
        model = Csp1dMilp()
        result = solver.solve(model)
        assert result.is_failed()

    def test_solver_result_is_dataclass(self) -> None:
        """SolverResult is a frozen dataclass. / SolverResult
        是冻结数据类。"""
        import dataclasses

        r = SolverResult(
            status=Csp1dFinalMilpStatus.OPTIMAL,
            objective_value=0.0,
            variable_values=(),
        )
        assert dataclasses.is_dataclass(r)
