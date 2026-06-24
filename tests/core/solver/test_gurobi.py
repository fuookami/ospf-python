"""Gurobi 求解器测试 / Gurobi solver tests.

使用 pytest.importorskip 在 gurobipy 未安装时优雅跳过。
Uses pytest.importorskip to skip gracefully when gurobipy
is not installed.
"""

from __future__ import annotations

import pytest

gurobipy = pytest.importorskip("gurobipy")

from ospf_python.core.solver.config.gurobi_solver_config import (
    GurobiSolverConfig,
)
from ospf_python.core.solver.gurobi.gurobi_benders_decomposition_solver import (
    GurobiBendersDecompositionSolver,
)
from ospf_python.core.solver.gurobi.gurobi_column_generation_solver import (
    GurobiColumnGenerationSolver,
)
from ospf_python.core.solver.gurobi.gurobi_constraint import (
    GurobiConstraint,
)
from ospf_python.core.solver.gurobi.gurobi_linear_solver import (
    GurobiLinearSolver,
)
from ospf_python.core.solver.gurobi.gurobi_quadratic_solver import (
    GurobiQuadraticSolver,
)
from ospf_python.core.solver.gurobi.gurobi_solver import (
    GurobiSolver,
)
from ospf_python.core.solver.gurobi.gurobi_solver_call_back import (
    GurobiSolverCallBack,
)
from ospf_python.core.solver.gurobi.gurobi_variable import (
    GurobiVariable,
)
from ospf_python.core.solver.gurobi.plugin_solver_async import (
    PluginSolverAsync,
)
from ospf_python.core.solver.output.solver_status import (
    SolverStatus,
)

# ============================================================
# GurobiSolverConfig tests
# ============================================================


class TestGurobiSolverConfig:
    """GurobiSolverConfig 测试 / Config tests."""

    def test_default_values(self) -> None:
        """默认值正确 / Default values correct."""
        cfg = GurobiSolverConfig()
        assert cfg.name == "gurobi"
        assert cfg.threads == 1
        assert cfg.mip_gap == 1e-4
        assert cfg.log_to_console is False

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        cfg = GurobiSolverConfig()
        with pytest.raises(AttributeError):
            cfg.name = "new"  # type: ignore[misc]


# ============================================================
# GurobiVariable tests
# ============================================================


class TestGurobiVariable:
    """GurobiVariable 冻结数据类测试 / Frozen dataclass
    tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        gv = GurobiVariable(
            var=None,
            name="x",
            vtype="C",
        )
        with pytest.raises(AttributeError):
            gv.name = "y"  # type: ignore[misc]

    def test_continuous_type(self) -> None:
        """连续变量类型 / Continuous variable type."""
        gv = GurobiVariable(
            var=None,
            name="x",
            vtype="C",
        )
        assert gv.is_continuous is True
        assert gv.is_integer is False
        assert gv.is_binary is False

    def test_integer_type(self) -> None:
        """整数变量类型 / Integer variable type."""
        gv = GurobiVariable(
            var=None,
            name="y",
            vtype="I",
        )
        assert gv.is_integer is True
        assert gv.is_continuous is False

    def test_binary_type(self) -> None:
        """二进制变量类型 / Binary variable type."""
        gv = GurobiVariable(
            var=None,
            name="z",
            vtype="B",
        )
        assert gv.is_binary is True
        assert gv.is_integer is True

    def test_bounds(self) -> None:
        """变量边界 / Variable bounds."""
        gv = GurobiVariable(
            var=None,
            name="x",
            lb=0.0,
            ub=10.0,
            vtype="C",
        )
        assert gv.lb == 0.0
        assert gv.ub == 10.0


# ============================================================
# GurobiConstraint tests
# ============================================================


class TestGurobiConstraint:
    """GurobiConstraint 冻结数据类测试 / Frozen dataclass
    tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        gc = GurobiConstraint(
            constr=None,
            name="c1",
        )
        with pytest.raises(AttributeError):
            gc.name = "c2"  # type: ignore[misc]

    def test_equality(self) -> None:
        """等式约束 / Equality constraint."""
        gc = GurobiConstraint(
            constr=None,
            name="c1",
            sense="=",
            rhs=5.0,
        )
        assert gc.is_equality is True
        assert gc.is_inequality is False

    def test_less_equal(self) -> None:
        """小于等于约束 / Less-equal constraint."""
        gc = GurobiConstraint(
            constr=None,
            name="c1",
            sense="<=",
            rhs=10.0,
        )
        assert gc.is_less_equal is True
        assert gc.is_inequality is True

    def test_greater_equal(self) -> None:
        """大于等于约束 / Greater-equal constraint."""
        gc = GurobiConstraint(
            constr=None,
            name="c1",
            sense=">=",
            rhs=0.0,
        )
        assert gc.is_greater_equal is True


# ============================================================
# GurobiSolver tests
# ============================================================


class TestGurobiSolver:
    """GurobiSolver 基类测试 / Base class tests."""

    def test_name(self) -> None:
        """求解器名称 / Solver name."""
        solver = GurobiSolver()
        assert solver.name == "gurobi"

    def test_not_cleaned_initially(self) -> None:
        """初始未清理 / Initially not cleaned."""
        solver = GurobiSolver()
        assert solver.is_cleaned_up() is False

    def test_unknown_status_when_no_model(self) -> None:
        """无模型时状态为未知 / Status unknown when no
        model."""
        solver = GurobiSolver()
        assert solver.get_status() == SolverStatus.UNKNOWN

    def test_not_terminated_initially(self) -> None:
        """初始未终止 / Initially not terminated."""
        solver = GurobiSolver()
        assert solver.is_terminated() is False

    def test_cleanup(self) -> None:
        """清理资源 / Cleanup resources."""
        solver = GurobiSolver()
        solver.cleanup()
        assert solver.is_cleaned_up() is True
        assert solver.is_terminated() is True

    def test_solve_returns_error_for_generic_model(
        self,
    ) -> None:
        """通用模型返回错误 / Generic model returns error."""
        solver = GurobiSolver()
        result = solver.solve(object())
        assert result.status is SolverStatus.ERROR


# ============================================================
# GurobiLinearSolver tests
# ============================================================


class TestGurobiLinearSolver:
    """GurobiLinearSolver 测试 / Linear solver tests."""

    def test_name(self) -> None:
        """求解器名称 / Solver name."""
        solver = GurobiLinearSolver()
        assert solver.name == "gurobi"

    def test_supports_integer(self) -> None:
        """支持整数变量 / Supports integer."""
        solver = GurobiLinearSolver()
        assert solver.supports_integer() is True

    def test_no_integer_support(self) -> None:
        """不支持整数 / No integer support."""
        solver = GurobiLinearSolver(
            _supports_int=False,
        )
        assert solver.supports_integer() is False

    def test_create_gurobi_model(self) -> None:
        """创建 gurobipy 模型 / Create gurobipy model."""
        solver = GurobiLinearSolver()
        model = solver._get_or_create_model()
        assert model is not None
        solver.cleanup()

    def test_solve_simple_lp(self) -> None:
        """求解简单 LP / Solve a simple LP.

        min  x + 2y
        s.t. x + y <= 10
             x, y >= 0
        """
        solver = GurobiLinearSolver()
        m = solver._get_or_create_model()
        from gurobipy import GRB

        x = m.addVar(lb=0.0, name="x", vtype=GRB.CONTINUOUS)
        y = m.addVar(lb=0.0, name="y", vtype=GRB.CONTINUOUS)
        m.setObjective(x + 2 * y, GRB.MINIMIZE)
        m.addConstr(x + y <= 10, name="c1")
        m.update()

        from ospf_python.core.solver.solve_options import (
            SolveOptions,
        )

        result = solver.solve(m, options=SolveOptions())

        assert result.status is SolverStatus.OPTIMAL
        assert abs(result.objective) < 1e-6
        assert abs(result.values.get("x")) < 1e-6
        assert abs(result.values.get("y")) < 1e-6
        solver.cleanup()

    def test_solve_milp(self) -> None:
        """求解 MILP / Solve a MILP.

        min  x + y
        s.t. x + y >= 5
             x integer, y >= 0
        """
        solver = GurobiLinearSolver()
        m = solver._get_or_create_model()
        from gurobipy import GRB

        x = m.addVar(lb=0.0, name="x", vtype=GRB.INTEGER)
        y = m.addVar(lb=0.0, name="y", vtype=GRB.CONTINUOUS)
        m.setObjective(x + y, GRB.MINIMIZE)
        m.addConstr(x + y >= 5, name="c1")
        m.update()

        result = solver.solve(m)

        assert result.status is SolverStatus.OPTIMAL
        assert result.objective >= 5.0 - 1e-6
        solver.cleanup()


# ============================================================
# GurobiQuadraticSolver tests
# ============================================================


class TestGurobiQuadraticSolver:
    """GurobiQuadraticSolver 测试 / Quadratic solver
    tests."""

    def test_name(self) -> None:
        """求解器名称 / Solver name."""
        solver = GurobiQuadraticSolver()
        assert solver.name == "gurobi"

    def test_supports_quadratic_objective(self) -> None:
        """支持二次目标 / Supports quadratic objective."""
        solver = GurobiQuadraticSolver()
        assert solver.supports_quadratic_objective() is True

    def test_supports_quadratic_constraint(self) -> None:
        """支持二次约束 / Supports quadratic constraint."""
        solver = GurobiQuadraticSolver()
        assert solver.supports_quadratic_constraint() is True

    def test_solve_simple_qp(self) -> None:
        """求解简单 QP / Solve a simple QP.

        min  x^2 + y^2
        s.t. x + y >= 1
        """
        solver = GurobiQuadraticSolver()
        m = solver._get_or_create_model()
        from gurobipy import GRB

        x = m.addVar(lb=-GRB.INFINITY, name="x")
        y = m.addVar(lb=-GRB.INFINITY, name="y")
        m.setObjective(x * x + y * y, GRB.MINIMIZE)
        m.addConstr(x + y >= 1, name="c1")
        m.update()

        result = solver.solve(m)

        assert result.status is SolverStatus.OPTIMAL
        assert result.objective >= 0.0
        solver.cleanup()


# ============================================================
# GurobiColumnGenerationSolver tests
# ============================================================


class TestGurobiColumnGenerationSolver:
    """GurobiColumnGenerationSolver 测试 / Column
    generation solver tests."""

    def test_name(self) -> None:
        """求解器名称 / Solver name."""
        solver = GurobiColumnGenerationSolver()
        assert solver.name == "gurobi"

    def test_max_iterations(self) -> None:
        """最大迭代次数 / Maximum iterations."""
        solver = GurobiColumnGenerationSolver(
            max_iterations=50,
        )
        assert solver.max_iterations == 50

    def test_pricing_tolerance(self) -> None:
        """定价容差 / Pricing tolerance."""
        solver = GurobiColumnGenerationSolver(
            pricing_tolerance=1e-8,
        )
        assert solver.pricing_tolerance == 1e-8


# ============================================================
# GurobiBendersDecompositionSolver tests
# ============================================================


class TestGurobiBendersDecompositionSolver:
    """GurobiBendersDecompositionSolver 测试 / Benders
    decomposition solver tests."""

    def test_name(self) -> None:
        """求解器名称 / Solver name."""
        solver = GurobiBendersDecompositionSolver()
        assert solver.name == "gurobi"

    def test_max_iterations(self) -> None:
        """最大迭代次数 / Maximum iterations."""
        solver = GurobiBendersDecompositionSolver(
            max_iterations=200,
        )
        assert solver.max_iterations == 200

    def test_optimality_tolerance(self) -> None:
        """最优性容差 / Optimality tolerance."""
        solver = GurobiBendersDecompositionSolver(
            optimality_tolerance=1e-4,
        )
        assert solver.optimality_tolerance == 1e-4


# ============================================================
# GurobiSolverCallBack tests
# ============================================================


class TestGurobiSolverCallBack:
    """GurobiSolverCallBack 测试 / Callback handler
    tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        cb = GurobiSolverCallBack()
        with pytest.raises(AttributeError):
            cb.callbacks = {}  # type: ignore[misc]

    def test_no_callbacks_initially(self) -> None:
        """初始无回调 / No callbacks initially."""
        cb = GurobiSolverCallBack()
        assert cb.has_callbacks is False
        assert cb.callback_count == 0

    def test_register_lazy_constraint(self) -> None:
        """注册惰性约束回调 / Register lazy constraint."""
        cb = GurobiSolverCallBack()
        new_cb = cb.register_lazy_constraint(
            "lazy1",
            lambda _: None,
        )
        assert new_cb.has_callbacks is True
        assert new_cb.callback_count == 1
        # 原始实例不变 / Original unchanged
        assert cb.has_callbacks is False

    def test_register_heuristic(self) -> None:
        """注册启发式回调 / Register heuristic."""
        cb = GurobiSolverCallBack()
        new_cb = cb.register_heuristic(
            "heur1",
            lambda _: None,
        )
        assert new_cb.callback_count == 1

    def test_register_cutting_plane(self) -> None:
        """注册割平面回调 / Register cutting plane."""
        cb = GurobiSolverCallBack()
        new_cb = cb.register_cutting_plane(
            "cut1",
            lambda _: None,
        )
        assert new_cb.callback_count == 1

    def test_multiple_callbacks(self) -> None:
        """多个回调 / Multiple callbacks."""
        cb = GurobiSolverCallBack()
        cb = cb.register_lazy_constraint(
            "lazy1",
            lambda _: None,
        )
        cb = cb.register_heuristic(
            "heur1",
            lambda _: None,
        )
        assert cb.callback_count == 2


# ============================================================
# PluginSolverAsync tests
# ============================================================


class TestPluginSolverAsync:
    """PluginSolverAsync 测试 / Async wrapper tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        solver = GurobiLinearSolver()
        async_solver = PluginSolverAsync(solver=solver)
        with pytest.raises(AttributeError):
            async_solver.solver = solver  # type: ignore[misc]

    @pytest.mark.asyncio
    async def test_solve_async(self) -> None:
        """异步求解 / Async solve."""
        solver = GurobiLinearSolver()
        async_solver = PluginSolverAsync(solver=solver)

        from gurobipy import GRB

        m = solver._get_or_create_model()
        x = m.addVar(lb=0.0, name="x")
        m.setObjective(x, GRB.MINIMIZE)
        m.addConstr(x >= 0, name="c1")
        m.update()

        result = await async_solver.solve_async(m)
        assert result.status is SolverStatus.OPTIMAL
        solver.cleanup()

    @pytest.mark.asyncio
    async def test_cancel_returns_false(self) -> None:
        """取消返回 False / Cancel returns False."""
        solver = GurobiLinearSolver()
        async_solver = PluginSolverAsync(solver=solver)
        assert await async_solver.cancel() is False
