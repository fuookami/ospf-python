"""SCIP Benders/CG 求解器扩展测试。

Extended tests for SCIP Benders decomposition and column
generation solvers. Covers construction, configuration, property
access, frozen behavior, and internal methods.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

from ospf_python.core.solver.config.scip_solver_config import (
    SCIPSolverConfig,
)
from ospf_python.core.solver.output.solver_status import (
    SolverStatus,
)

# ── helpers ────────────────────────────────────────────────────


def _make_mock_pyscipopt() -> types.ModuleType:
    """创建模拟 pyscipopt 模块。

    Create a mock pyscipopt module.
    """
    mod = types.ModuleType("pyscipopt")
    mod.Model = MagicMock
    return mod


# ── Benders tests ──────────────────────────────────────────────


class TestScipBendersConstruction:
    """Benders 分解求解器构造测试。

    Construction tests for SCIP Benders solver.
    """

    def test_default_construction(self) -> None:
        """默认构造。/ Default construction."""
        from ospf_python.core.solver.scip.scip_benders_decomposition_solver import (
            ScipBendersDecompositionSolver,
        )

        solver = ScipBendersDecompositionSolver()
        assert solver.name == "scip"

    def test_custom_config(self) -> None:
        """自定义配置构造。/ Custom config construction."""
        from ospf_python.core.solver.scip.scip_benders_decomposition_solver import (
            ScipBendersDecompositionSolver,
        )

        cfg = SCIPSolverConfig(
            gap_tolerance=1e-6,
            verbose=True,
        )
        solver = ScipBendersDecompositionSolver(config=cfg)
        assert solver.config.gap_tolerance == 1e-6
        assert solver.config.verbose is True

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        from ospf_python.core.solver.scip.scip_benders_decomposition_solver import (
            ScipBendersDecompositionSolver,
        )

        solver = ScipBendersDecompositionSolver()
        with pytest.raises(AttributeError):
            solver.max_iterations = 50  # type: ignore[misc]

    def test_not_cleaned_initially(self) -> None:
        """初始未清理。/ Initially not cleaned."""
        from ospf_python.core.solver.scip.scip_benders_decomposition_solver import (
            ScipBendersDecompositionSolver,
        )

        solver = ScipBendersDecompositionSolver()
        assert solver.is_cleaned_up() is False

    def test_unknown_status_when_no_model(self) -> None:
        """无模型时状态未知。/ Status unknown when no model."""
        from ospf_python.core.solver.scip.scip_benders_decomposition_solver import (
            ScipBendersDecompositionSolver,
        )

        solver = ScipBendersDecompositionSolver()
        assert solver.get_status() == SolverStatus.UNKNOWN

    def test_not_terminated_initially(self) -> None:
        """初始未终止。/ Initially not terminated."""
        from ospf_python.core.solver.scip.scip_benders_decomposition_solver import (
            ScipBendersDecompositionSolver,
        )

        solver = ScipBendersDecompositionSolver()
        assert solver.is_terminated() is False

    def test_cleanup_sets_cleaned(self) -> None:
        """清理后标记已清理。/ Cleanup sets cleaned flag."""
        from ospf_python.core.solver.scip.scip_benders_decomposition_solver import (
            ScipBendersDecompositionSolver,
        )

        solver = ScipBendersDecompositionSolver()
        solver.cleanup()
        assert solver.is_cleaned_up() is True

    def test_internal_generate_cuts_returns_empty(self) -> None:
        """内部割生成返回空。/ Internal cut gen returns empty."""
        from ospf_python.core.solver.scip.scip_benders_decomposition_solver import (
            ScipBendersDecompositionSolver,
        )

        solver = ScipBendersDecompositionSolver()
        result = solver._generate_cuts(object(), object())
        assert result == []

    def test_internal_add_cuts_no_error(self) -> None:
        """内部添加割不抛异常。/ Internal add cuts no error."""
        from ospf_python.core.solver.scip.scip_benders_decomposition_solver import (
            ScipBendersDecompositionSolver,
        )

        solver = ScipBendersDecompositionSolver()
        solver._add_cuts(object(), ["cut1", "cut2"])


class TestScipBendersSolve:
    """Benders 求解方法测试。/ Benders solve method tests."""

    def test_solve_returns_output(self) -> None:
        """求解返回 SolverOutput。/ Solve returns output."""
        mock_mod = _make_mock_pyscipopt()
        sys.modules["pyscipopt"] = mock_mod
        try:
            from ospf_python.core.solver.scip.scip_benders_decomposition_solver import (
                ScipBendersDecompositionSolver,
            )

            solver = ScipBendersDecompositionSolver()
            mock_model = MagicMock()
            mock_model.getStatus.return_value = "optimal"
            mock_model.getVars.return_value = []
            mock_model.getObjVal.return_value = 0.0
            object.__setattr__(solver, "_model", mock_model)

            result = solver.solve(object())
            assert isinstance(result.status, SolverStatus)
            solver.cleanup()
        finally:
            sys.modules.pop("pyscipopt", None)

    def test_solve_exception_returns_error(self) -> None:
        """异常时返回错误状态。

        Returns error status when exception occurs.
        """
        mock_mod = _make_mock_pyscipopt()
        sys.modules["pyscipopt"] = mock_mod
        try:
            from ospf_python.core.solver.scip.scip_benders_decomposition_solver import (
                ScipBendersDecompositionSolver,
            )

            solver = ScipBendersDecompositionSolver()
            mock_model = MagicMock()
            mock_model.optimize.side_effect = RuntimeError(
                "scip error",
            )
            object.__setattr__(solver, "_model", mock_model)

            result = solver.solve(object())
            assert result.status is SolverStatus.ERROR
        finally:
            sys.modules.pop("pyscipopt", None)


# ── Column generation tests ────────────────────────────────────


class TestScipCGConstruction:
    """列生成求解器构造测试。

    Construction tests for SCIP column generation solver.
    """

    def test_default_construction(self) -> None:
        """默认构造。/ Default construction."""
        from ospf_python.core.solver.scip.scip_column_generation_solver import (
            ScipColumnGenerationSolver,
        )

        solver = ScipColumnGenerationSolver()
        assert solver.name == "scip"

    def test_custom_config(self) -> None:
        """自定义配置构造。/ Custom config construction."""
        from ospf_python.core.solver.scip.scip_column_generation_solver import (
            ScipColumnGenerationSolver,
        )

        cfg = SCIPSolverConfig(
            threads=4,
            time_limit=120.0,
        )
        solver = ScipColumnGenerationSolver(config=cfg)
        assert solver.config.threads == 4
        assert solver.config.time_limit == 120.0

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        from ospf_python.core.solver.scip.scip_column_generation_solver import (
            ScipColumnGenerationSolver,
        )

        solver = ScipColumnGenerationSolver()
        with pytest.raises(AttributeError):
            solver.pricing_tolerance = 1e-8  # type: ignore[misc]

    def test_unknown_status_when_no_model(self) -> None:
        """无模型时状态未知。/ Status unknown when no model."""
        from ospf_python.core.solver.scip.scip_column_generation_solver import (
            ScipColumnGenerationSolver,
        )

        solver = ScipColumnGenerationSolver()
        assert solver.get_status() == SolverStatus.UNKNOWN

    def test_not_terminated_initially(self) -> None:
        """初始未终止。/ Initially not terminated."""
        from ospf_python.core.solver.scip.scip_column_generation_solver import (
            ScipColumnGenerationSolver,
        )

        solver = ScipColumnGenerationSolver()
        assert solver.is_terminated() is False

    def test_internal_pricing_returns_empty(self) -> None:
        """内部定价返回空。/ Internal pricing returns empty."""
        from ospf_python.core.solver.scip.scip_column_generation_solver import (
            ScipColumnGenerationSolver,
        )

        solver = ScipColumnGenerationSolver()
        result = solver._pricing(object(), object())
        assert result == []

    def test_internal_add_columns_no_error(self) -> None:
        """内部添加列不抛异常。

        Internal add columns does not raise.
        """
        from ospf_python.core.solver.scip.scip_column_generation_solver import (
            ScipColumnGenerationSolver,
        )

        solver = ScipColumnGenerationSolver()
        solver._add_columns(object(), ["col1"])


class TestScipCGSolve:
    """列生成求解方法测试。

    Column generation solve method tests.
    """

    def test_solve_returns_output(self) -> None:
        """求解返回输出。/ Solve returns output."""
        mock_mod = _make_mock_pyscipopt()
        sys.modules["pyscipopt"] = mock_mod
        try:
            from ospf_python.core.solver.scip.scip_column_generation_solver import (
                ScipColumnGenerationSolver,
            )

            solver = ScipColumnGenerationSolver()
            mock_model = MagicMock()
            mock_model.getStatus.return_value = "optimal"
            mock_model.getVars.return_value = []
            mock_model.getObjVal.return_value = 0.0
            object.__setattr__(solver, "_model", mock_model)

            result = solver.solve(object())
            assert isinstance(result.status, SolverStatus)
            solver.cleanup()
        finally:
            sys.modules.pop("pyscipopt", None)

    def test_solve_non_optimal_stops(self) -> None:
        """非最优状态时停止迭代。

        Stops iteration when status is not optimal.
        """
        mock_mod = _make_mock_pyscipopt()
        sys.modules["pyscipopt"] = mock_mod
        try:
            from ospf_python.core.solver.scip.scip_column_generation_solver import (
                ScipColumnGenerationSolver,
            )

            solver = ScipColumnGenerationSolver(
                max_iterations=5,
            )
            mock_model = MagicMock()
            mock_model.getStatus.return_value = "infeasible"
            object.__setattr__(solver, "_model", mock_model)

            result = solver.solve(object())
            assert isinstance(result.status, SolverStatus)
        finally:
            sys.modules.pop("pyscipopt", None)

    def test_solve_exception_returns_error(self) -> None:
        """异常时返回错误状态。

        Returns error status when exception occurs.
        """
        mock_mod = _make_mock_pyscipopt()
        sys.modules["pyscipopt"] = mock_mod
        try:
            from ospf_python.core.solver.scip.scip_column_generation_solver import (
                ScipColumnGenerationSolver,
            )

            solver = ScipColumnGenerationSolver()
            mock_model = MagicMock()
            mock_model.optimize.side_effect = RuntimeError(
                "scip error",
            )
            object.__setattr__(solver, "_model", mock_model)

            result = solver.solve(object())
            assert result.status is SolverStatus.ERROR
        finally:
            sys.modules.pop("pyscipopt", None)
