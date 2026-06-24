"""SolverOutput 测试。

测试求解器输出的创建、状态检测和工厂方法。
Tests SolverOutput creation, status detection, and factories.
"""

from __future__ import annotations

import pytest

from ospf_python.core.solver.output.solver_output import (
    SolverOutput,
)
from ospf_python.core.solver.output.solver_status import (
    SolverStatus,
)
from ospf_python.core.solver.value.solve_value import SolveValue


class TestSolverOutputCreation:
    """创建测试 / Creation tests."""

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        out = SolverOutput(status=SolverStatus.OPTIMAL)
        with pytest.raises(AttributeError):
            out.objective = 99.0  # type: ignore[misc]

    def test_is_optimal(self) -> None:
        """最优状态检测。/ Optimal status detection."""
        out = SolverOutput(status=SolverStatus.OPTIMAL)
        assert out.is_optimal is True

    def test_is_infeasible(self) -> None:
        """不可行状态检测。/ Infeasible status detection."""
        out = SolverOutput(status=SolverStatus.INFEASIBLE)
        assert out.is_infeasible is True


class TestSolverOutputFactories:
    """工厂方法测试 / Factory method tests."""

    def test_optimal_factory(self) -> None:
        """最优工厂方法。/ Optimal factory."""
        sv = SolveValue(values={"x": 1.0})
        out = SolverOutput.optimal(42.0, sv)
        assert out.status is SolverStatus.OPTIMAL
        assert out.objective == 42.0

    def test_infeasible_factory(self) -> None:
        """不可行工厂方法。/ Infeasible factory."""
        out = SolverOutput.infeasible()
        assert out.status is SolverStatus.INFEASIBLE

    def test_timeout_factory(self) -> None:
        """超时工厂方法。/ Timeout factory."""
        out = SolverOutput.timeout(objective=10.0)
        assert out.status is SolverStatus.TIMEOUT
        assert out.objective == 10.0
