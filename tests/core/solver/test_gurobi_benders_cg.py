"""Gurobi Benders/CG 求解器扩展测试。

Extended tests for Gurobi Benders decomposition and column
generation solvers. Covers construction, configuration, property
access, frozen behavior, and internal methods.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

from ospf_python.core.solver.config.gurobi_solver_config import (
    GurobiSolverConfig,
)
from ospf_python.core.solver.output.solver_status import (
    SolverStatus,
)

# ── helpers ────────────────────────────────────────────────────


def _make_mock_gurobipy() -> types.ModuleType:
    """创建模拟 gurobipy 模块。

    Create a mock gurobipy module.
    """
    mod = types.ModuleType("gurobipy")
    exc = type("GurobiError", (Exception,), {})
    mod.GurobiError = exc
    mod.GRB = MagicMock()
    mod.GRB.OPTIMAL = 2
    mod.Model = MagicMock
    return mod


# ── Benders tests ──────────────────────────────────────────────


class TestGurobiBendersConstruction:
    """Benders 分解求解器构造测试。

    Construction tests for Benders decomposition solver.
    """

    def test_default_construction(self) -> None:
        """默认构造。/ Default construction."""
        from ospf_python.core.solver.gurobi.gurobi_benders_decomposition_solver import (
            GurobiBendersDecompositionSolver,
        )

        solver = GurobiBendersDecompositionSolver()
        assert solver.name == "gurobi"

    def test_custom_config(self) -> None:
        """自定义配置构造。/ Custom config construction."""
        from ospf_python.core.solver.gurobi.gurobi_benders_decomposition_solver import (
            GurobiBendersDecompositionSolver,
        )

        cfg = GurobiSolverConfig(
            threads=4,
            mip_gap=1e-6,
        )
        solver = GurobiBendersDecompositionSolver(config=cfg)
        assert solver.config.threads == 4
        assert solver.config.mip_gap == 1e-6

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        from ospf_python.core.solver.gurobi.gurobi_benders_decomposition_solver import (
            GurobiBendersDecompositionSolver,
        )

        solver = GurobiBendersDecompositionSolver()
        with pytest.raises(AttributeError):
            solver.max_iterations = 50  # type: ignore[misc]

    def test_not_cleaned_initially(self) -> None:
        """初始未清理。/ Initially not cleaned."""
        from ospf_python.core.solver.gurobi.gurobi_benders_decomposition_solver import (
            GurobiBendersDecompositionSolver,
        )

        solver = GurobiBendersDecompositionSolver()
        assert solver.is_cleaned_up() is False

    def test_cleanup_sets_cleaned(self) -> None:
        """清理后标记已清理。/ Cleanup sets cleaned flag."""
        from ospf_python.core.solver.gurobi.gurobi_benders_decomposition_solver import (
            GurobiBendersDecompositionSolver,
        )

        solver = GurobiBendersDecompositionSolver()
        solver.cleanup()
        assert solver.is_cleaned_up() is True

    def test_internal_generate_cuts_returns_empty(self) -> None:
        """内部割生成返回空。/ Internal cut gen returns empty."""
        from ospf_python.core.solver.gurobi.gurobi_benders_decomposition_solver import (
            GurobiBendersDecompositionSolver,
        )

        solver = GurobiBendersDecompositionSolver()
        result = solver._generate_cuts(object(), object())
        assert result == []

    def test_internal_add_cuts_no_error(self) -> None:
        """内部添加割不抛异常。/ Internal add cuts no error."""
        from ospf_python.core.solver.gurobi.gurobi_benders_decomposition_solver import (
            GurobiBendersDecompositionSolver,
        )

        solver = GurobiBendersDecompositionSolver()
        solver._add_cuts(object(), ["cut1", "cut2"])


class TestGurobiBendersSolve:
    """Benders 求解方法测试。/ Benders solve method tests."""

    def test_solve_returns_output(self) -> None:
        """求解返回 SolverOutput。/ Solve returns output."""
        mock_mod = _make_mock_gurobipy()
        sys.modules["gurobipy"] = mock_mod
        try:
            from ospf_python.core.solver.gurobi.gurobi_benders_decomposition_solver import (
                GurobiBendersDecompositionSolver,
            )

            solver = GurobiBendersDecompositionSolver()
            mock_model = MagicMock()
            mock_model.Status = mock_mod.GRB.OPTIMAL
            mock_model.getVars.return_value = []
            mock_model.ObjVal = 0.0
            object.__setattr__(solver, "_model", mock_model)

            result = solver.solve(object())
            assert isinstance(result.status, SolverStatus)
            solver.cleanup()
        finally:
            sys.modules.pop("gurobipy", None)

    def test_solve_non_optimal_stops(self) -> None:
        """非最优状态时停止。/ Stops on non-optimal status."""
        mock_mod = _make_mock_gurobipy()
        sys.modules["gurobipy"] = mock_mod
        try:
            from ospf_python.core.solver.gurobi.gurobi_benders_decomposition_solver import (
                GurobiBendersDecompositionSolver,
            )

            solver = GurobiBendersDecompositionSolver()
            mock_model = MagicMock()
            # Status 不等于 GRB.OPTIMAL 导致返回非最优
            mock_model.Status = -1
            object.__setattr__(solver, "_model", mock_model)

            result = solver.solve(object())
            assert isinstance(result.status, SolverStatus)
        finally:
            sys.modules.pop("gurobipy", None)


# ── Column generation tests ────────────────────────────────────


class TestGurobiCGConstruction:
    """列生成求解器构造测试。

    Construction tests for column generation solver.
    """

    def test_default_construction(self) -> None:
        """默认构造。/ Default construction."""
        from ospf_python.core.solver.gurobi.gurobi_column_generation_solver import (
            GurobiColumnGenerationSolver,
        )

        solver = GurobiColumnGenerationSolver()
        assert solver.name == "gurobi"

    def test_custom_config(self) -> None:
        """自定义配置构造。/ Custom config construction."""
        from ospf_python.core.solver.gurobi.gurobi_column_generation_solver import (
            GurobiColumnGenerationSolver,
        )

        cfg = GurobiSolverConfig(
            threads=8,
            log_to_console=True,
        )
        solver = GurobiColumnGenerationSolver(config=cfg)
        assert solver.config.threads == 8
        assert solver.config.log_to_console is True

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        from ospf_python.core.solver.gurobi.gurobi_column_generation_solver import (
            GurobiColumnGenerationSolver,
        )

        solver = GurobiColumnGenerationSolver()
        with pytest.raises(AttributeError):
            solver.pricing_tolerance = 1e-8  # type: ignore[misc]

    def test_unknown_status_when_no_model(self) -> None:
        """无模型时状态未知。/ Status unknown when no model."""
        from ospf_python.core.solver.gurobi.gurobi_column_generation_solver import (
            GurobiColumnGenerationSolver,
        )

        solver = GurobiColumnGenerationSolver()
        assert solver.get_status() == SolverStatus.UNKNOWN

    def test_not_terminated_initially(self) -> None:
        """初始未终止。/ Initially not terminated."""
        from ospf_python.core.solver.gurobi.gurobi_column_generation_solver import (
            GurobiColumnGenerationSolver,
        )

        solver = GurobiColumnGenerationSolver()
        assert solver.is_terminated() is False

    def test_internal_pricing_returns_empty(self) -> None:
        """内部定价返回空。/ Internal pricing returns empty."""
        from ospf_python.core.solver.gurobi.gurobi_column_generation_solver import (
            GurobiColumnGenerationSolver,
        )

        solver = GurobiColumnGenerationSolver()
        result = solver._pricing(object(), object())
        assert result == []

    def test_internal_add_columns_no_error(self) -> None:
        """内部添加列不抛异常。

        Internal add columns does not raise.
        """
        from ospf_python.core.solver.gurobi.gurobi_column_generation_solver import (
            GurobiColumnGenerationSolver,
        )

        solver = GurobiColumnGenerationSolver()
        solver._add_columns(object(), ["col1"])


class TestGurobiCGSolve:
    """列生成求解方法测试。

    Column generation solve method tests.
    """

    def test_solve_returns_output(self) -> None:
        """求解返回输出。/ Solve returns output."""
        mock_mod = _make_mock_gurobipy()
        sys.modules["gurobipy"] = mock_mod
        try:
            from ospf_python.core.solver.gurobi.gurobi_column_generation_solver import (
                GurobiColumnGenerationSolver,
            )

            solver = GurobiColumnGenerationSolver()
            mock_model = MagicMock()
            mock_model.Status = mock_mod.GRB.OPTIMAL
            mock_model.getVars.return_value = []
            mock_model.ObjVal = 0.0
            object.__setattr__(solver, "_model", mock_model)

            result = solver.solve(object())
            assert isinstance(result.status, SolverStatus)
            solver.cleanup()
        finally:
            sys.modules.pop("gurobipy", None)

    def test_solve_non_optimal_stops(self) -> None:
        """非最优状态时停止迭代。

        Stops iteration when status is not optimal.
        """
        mock_mod = _make_mock_gurobipy()
        sys.modules["gurobipy"] = mock_mod
        try:
            from ospf_python.core.solver.gurobi.gurobi_column_generation_solver import (
                GurobiColumnGenerationSolver,
            )

            solver = GurobiColumnGenerationSolver(
                max_iterations=5,
            )
            mock_model = MagicMock()
            mock_model.Status = -1
            object.__setattr__(solver, "_model", mock_model)

            result = solver.solve(object())
            assert isinstance(result.status, SolverStatus)
        finally:
            sys.modules.pop("gurobipy", None)
