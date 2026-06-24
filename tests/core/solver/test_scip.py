"""SCIP 求解器测试 / SCIP solver tests.

使用 pytest.importorskip 在 pyscipopt 未安装时优雅跳过。
Uses pytest.importorskip to skip gracefully when pyscipopt
is not installed.
"""

from __future__ import annotations

import pytest

pyscipopt = pytest.importorskip("pyscipopt")

from ospf_python.core.solver.config.scip_solver_config import (
    SCIPSolverConfig,
)
from ospf_python.core.solver.output.solver_status import (
    SolverStatus,
)
from ospf_python.core.solver.scip.plugin_solver_async import (
    PluginSolverAsync,
)
from ospf_python.core.solver.scip.scip_benders_decomposition_solver import (
    ScipBendersDecompositionSolver,
)
from ospf_python.core.solver.scip.scip_column_generation_solver import (
    ScipColumnGenerationSolver,
)
from ospf_python.core.solver.scip.scip_linear_solver import (
    ScipLinearSolver,
)
from ospf_python.core.solver.scip.scip_quadratic_solver import (
    ScipQuadraticSolver,
)
from ospf_python.core.solver.scip.scip_solver import (
    ScipSolver,
)
from ospf_python.core.solver.scip.scip_solver_call_back import (
    ScipSolverCallBack,
)
from ospf_python.core.solver.scip.scip_variable import (
    ScipVariable,
)

# ============================================================
# SCIPSolverConfig tests
# ============================================================


class TestSCIPSolverConfig:
    """SCIPSolverConfig 测试 / Config tests."""

    def test_default_values(self) -> None:
        """默认值正确 / Default values correct."""
        cfg = SCIPSolverConfig()
        assert cfg.name == "scip"
        assert cfg.threads == 1
        assert cfg.gap_tolerance == 1e-4
        assert cfg.verbose is False

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        cfg = SCIPSolverConfig()
        with pytest.raises(AttributeError):
            cfg.name = "new"  # type: ignore[misc]


# ============================================================
# ScipVariable tests
# ============================================================


class TestScipVariable:
    """ScipVariable 冻结数据类测试 / Frozen dataclass
    tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        sv = ScipVariable(
            var=None,
            name="x",
            vtype="CONTINUOUS",
        )
        with pytest.raises(AttributeError):
            sv.name = "y"  # type: ignore[misc]

    def test_continuous_type(self) -> None:
        """连续变量类型 / Continuous variable type."""
        sv = ScipVariable(
            var=None,
            name="x",
            vtype="CONTINUOUS",
        )
        assert sv.is_continuous is True
        assert sv.is_integer is False
        assert sv.is_binary is False

    def test_integer_type(self) -> None:
        """整数变量类型 / Integer variable type."""
        sv = ScipVariable(
            var=None,
            name="y",
            vtype="INTEGER",
        )
        assert sv.is_integer is True
        assert sv.is_continuous is False

    def test_binary_type(self) -> None:
        """二进制变量类型 / Binary variable type."""
        sv = ScipVariable(
            var=None,
            name="z",
            vtype="BINARY",
        )
        assert sv.is_binary is True
        assert sv.is_integer is True

    def test_bounds(self) -> None:
        """变量边界 / Variable bounds."""
        sv = ScipVariable(
            var=None,
            name="x",
            lb=0.0,
            ub=10.0,
            vtype="CONTINUOUS",
        )
        assert sv.lb == 0.0
        assert sv.ub == 10.0


# ============================================================
# ScipSolver tests
# ============================================================


class TestScipSolver:
    """ScipSolver 基类测试 / Base class tests."""

    def test_name(self) -> None:
        """求解器名称 / Solver name."""
        solver = ScipSolver()
        assert solver.name == "scip"

    def test_not_cleaned_initially(self) -> None:
        """初始未清理 / Initially not cleaned."""
        solver = ScipSolver()
        assert solver.is_cleaned_up() is False

    def test_unknown_status_when_no_model(self) -> None:
        """无模型时状态为未知 / Status unknown when no
        model."""
        solver = ScipSolver()
        assert solver.get_status() == SolverStatus.UNKNOWN

    def test_not_terminated_initially(self) -> None:
        """初始未终止 / Initially not terminated."""
        solver = ScipSolver()
        assert solver.is_terminated() is False

    def test_cleanup(self) -> None:
        """清理资源 / Cleanup resources."""
        solver = ScipSolver()
        solver.cleanup()
        assert solver.is_cleaned_up() is True
        assert solver.is_terminated() is True

    def test_solve_returns_error_for_generic_model(
        self,
    ) -> None:
        """通用模型返回错误 / Generic model returns error."""
        solver = ScipSolver()
        result = solver.solve(object())
        assert result.status is SolverStatus.ERROR


# ============================================================
# ScipLinearSolver tests
# ============================================================


class TestScipLinearSolver:
    """ScipLinearSolver 测试 / Linear solver tests."""

    def test_name(self) -> None:
        """求解器名称 / Solver name."""
        solver = ScipLinearSolver()
        assert solver.name == "scip"

    def test_supports_integer(self) -> None:
        """支持整数变量 / Supports integer."""
        solver = ScipLinearSolver()
        assert solver.supports_integer() is True

    def test_no_integer_support(self) -> None:
        """不支持整数 / No integer support."""
        solver = ScipLinearSolver(
            _supports_int=False,
        )
        assert solver.supports_integer() is False

    def test_create_scip_model(self) -> None:
        """创建 SCIP 模型 / Create SCIP model."""
        solver = ScipLinearSolver()
        model = solver._get_or_create_model()
        assert model is not None
        solver.cleanup()

    def test_solve_simple_lp(self) -> None:
        """求解简单 LP / Solve a simple LP.

        min  x + 2y
        s.t. x + y <= 10
             x, y >= 0
        """
        solver = ScipLinearSolver()
        m = solver._get_or_create_model()

        x = m.addVar(
            lb=0.0,
            name="x",
            vtype="CONTINUOUS",
        )
        y = m.addVar(
            lb=0.0,
            name="y",
            vtype="CONTINUOUS",
        )
        m.setObjective(x + 2 * y, "minimize")
        m.addCons(x + y <= 10, name="c1")

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
        solver = ScipLinearSolver()
        m = solver._get_or_create_model()

        x = m.addVar(
            lb=0.0,
            name="x",
            vtype="INTEGER",
        )
        y = m.addVar(
            lb=0.0,
            name="y",
            vtype="CONTINUOUS",
        )
        m.setObjective(x + y, "minimize")
        m.addCons(x + y >= 5, name="c1")

        result = solver.solve(m)

        assert result.status is SolverStatus.OPTIMAL
        assert result.objective >= 5.0 - 1e-6
        solver.cleanup()


# ============================================================
# ScipQuadraticSolver tests
# ============================================================


class TestScipQuadraticSolver:
    """ScipQuadraticSolver 测试 / Quadratic solver
    tests."""

    def test_name(self) -> None:
        """求解器名称 / Solver name."""
        solver = ScipQuadraticSolver()
        assert solver.name == "scip"

    def test_supports_quadratic_objective(self) -> None:
        """支持二次目标 / Supports quadratic objective."""
        solver = ScipQuadraticSolver()
        assert solver.supports_quadratic_objective() is True

    def test_supports_quadratic_constraint(self) -> None:
        """支持二次约束 / Supports quadratic constraint."""
        solver = ScipQuadraticSolver()
        assert solver.supports_quadratic_constraint() is True


# ============================================================
# ScipColumnGenerationSolver tests
# ============================================================


class TestScipColumnGenerationSolver:
    """ScipColumnGenerationSolver 测试 / Column generation
    solver tests."""

    def test_name(self) -> None:
        """求解器名称 / Solver name."""
        solver = ScipColumnGenerationSolver()
        assert solver.name == "scip"

    def test_max_iterations(self) -> None:
        """最大迭代次数 / Maximum iterations."""
        solver = ScipColumnGenerationSolver(
            max_iterations=50,
        )
        assert solver.max_iterations == 50

    def test_pricing_tolerance(self) -> None:
        """定价容差 / Pricing tolerance."""
        solver = ScipColumnGenerationSolver(
            pricing_tolerance=1e-8,
        )
        assert solver.pricing_tolerance == 1e-8


# ============================================================
# ScipBendersDecompositionSolver tests
# ============================================================


class TestScipBendersDecompositionSolver:
    """ScipBendersDecompositionSolver 测试 / Benders
    decomposition solver tests."""

    def test_name(self) -> None:
        """求解器名称 / Solver name."""
        solver = ScipBendersDecompositionSolver()
        assert solver.name == "scip"

    def test_max_iterations(self) -> None:
        """最大迭代次数 / Maximum iterations."""
        solver = ScipBendersDecompositionSolver(
            max_iterations=200,
        )
        assert solver.max_iterations == 200

    def test_optimality_tolerance(self) -> None:
        """最优性容差 / Optimality tolerance."""
        solver = ScipBendersDecompositionSolver(
            optimality_tolerance=1e-4,
        )
        assert solver.optimality_tolerance == 1e-4


# ============================================================
# ScipSolverCallBack tests
# ============================================================


class TestScipSolverCallBack:
    """ScipSolverCallBack 测试 / Callback handler
    tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        cb = ScipSolverCallBack()
        with pytest.raises(AttributeError):
            cb.callbacks = {}  # type: ignore[misc]

    def test_no_callbacks_initially(self) -> None:
        """初始无回调 / No callbacks initially."""
        cb = ScipSolverCallBack()
        assert cb.has_callbacks is False
        assert cb.callback_count == 0

    def test_register_node_selector(self) -> None:
        """注册节点选择回调 / Register node selector."""
        cb = ScipSolverCallBack()
        new_cb = cb.register_node_selector(
            "ns1",
            lambda _: None,
        )
        assert new_cb.has_callbacks is True
        assert new_cb.callback_count == 1
        # 原始实例不变 / Original unchanged
        assert cb.has_callbacks is False

    def test_register_branching_rule(self) -> None:
        """注册分支规则回调 / Register branching rule."""
        cb = ScipSolverCallBack()
        new_cb = cb.register_branching_rule(
            "br1",
            lambda _: None,
        )
        assert new_cb.callback_count == 1

    def test_register_event_handler(self) -> None:
        """注册事件处理器回调 / Register event handler."""
        cb = ScipSolverCallBack()
        new_cb = cb.register_event_handler(
            "eh1",
            lambda _: None,
        )
        assert new_cb.callback_count == 1

    def test_multiple_callbacks(self) -> None:
        """多个回调 / Multiple callbacks."""
        cb = ScipSolverCallBack()
        cb = cb.register_node_selector(
            "ns1",
            lambda _: None,
        )
        cb = cb.register_branching_rule(
            "br1",
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
        solver = ScipLinearSolver()
        async_solver = PluginSolverAsync(solver=solver)
        with pytest.raises(AttributeError):
            async_solver.solver = solver  # type: ignore[misc]

    @pytest.mark.asyncio
    async def test_solve_async(self) -> None:
        """异步求解 / Async solve."""
        solver = ScipLinearSolver()
        async_solver = PluginSolverAsync(solver=solver)

        m = solver._get_or_create_model()
        x = m.addVar(lb=0.0, name="x", vtype="CONTINUOUS")
        m.setObjective(x, "minimize")
        m.addCons(x >= 0, name="c1")

        result = await async_solver.solve_async(m)
        assert result.status is SolverStatus.OPTIMAL
        solver.cleanup()

    @pytest.mark.asyncio
    async def test_cancel_returns_false(self) -> None:
        """取消返回 False / Cancel returns False."""
        solver = ScipLinearSolver()
        async_solver = PluginSolverAsync(solver=solver)
        assert await async_solver.cancel() is False
