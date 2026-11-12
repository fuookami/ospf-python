"""Gurobi 求解器测试 / Gurobi solver tests.

使用 pytest.importorskip 在 gurobipy 未安装时优雅跳过。
Uses pytest.importorskip to skip gracefully when gurobipy
is not installed.
"""

from __future__ import annotations

import pytest

gurobipy = pytest.importorskip("gurobipy")

from ospf_python.core.model.intermediate.linear_triad_model import (
    LinearTriadModel,
)
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

    def test_solve_lp_publishes_real_duals_by_constraint_name(self) -> None:
        """LP 发布真实对偶值 / LP publishes real duals.

        min  2x + y
        s.t. x + y >= 4     (active)
             x + 2y >= 6    (slack)
             x, y >= 0
        """
        solver = GurobiLinearSolver()
        m = solver._get_or_create_model()
        from gurobipy import GRB

        x = m.addVar(lb=0.0, name="x", vtype=GRB.CONTINUOUS)
        y = m.addVar(lb=0.0, name="y", vtype=GRB.CONTINUOUS)
        m.setObjective(2 * x + y, GRB.MINIMIZE)
        m.addConstr(x + y >= 4, name="c1")
        m.addConstr(x + 2 * y >= 6, name="c2")
        m.update()

        result = solver.solve(m)

        assert result.status is SolverStatus.OPTIMAL
        assert result.dual_values == pytest.approx({"c1": 1.0, "c2": 0.0})
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
        assert result.dual_values is None
        solver.cleanup()

    def test_solve_linear_triad_materializes_variables_and_constraints(
        self,
    ) -> None:
        """线性三元组物化后返回真实 primal/dual。"""
        solver = GurobiLinearSolver()
        model = LinearTriadModel(
            name="triad",
            variables=["x", "y"],
            objective={"x": 2.0, "y": 3.0},
            constraints={
                "c1": {"x": 1.0, "y": 1.0},
                "c2": {"x": 1.0, "y": 2.0},
            },
            rhs={"c1": 4.0, "c2": 6.0},
            sense={"c1": ">=", "c2": ">="},
            lower_bounds={"x": 0.0, "y": 0.0},
            upper_bounds={"x": float("inf"), "y": float("inf")},
        )

        result = solver.solve(model)

        assert result.status is SolverStatus.OPTIMAL
        assert result.objective == pytest.approx(10.0)
        assert result.values.get("x") == pytest.approx(2.0)
        assert result.values.get("y") == pytest.approx(2.0)
        assert result.dual_values is not None
        assert result.dual_values["c1"] == pytest.approx(1.0)
        assert result.dual_values["c2"] == pytest.approx(1.0)
        solver.cleanup()

    @pytest.mark.parametrize(
        ("variable_type", "rhs", "expected"),
        [
            ("continuous", 0.5, 0.5),
            ("binary", 0.5, 1.0),
            ("integer", 1.5, 2.0),
        ],
    )
    def test_solve_linear_triad_honors_variable_types(
        self,
        variable_type: str,
        rhs: float,
        expected: float,
    ) -> None:
        """连续、二元和整数类型得到不同真实解。"""
        solver = GurobiLinearSolver()
        model = LinearTriadModel(
            name=f"triad-{variable_type}",
            variables=["x"],
            constraints={"lower": {"x": 1.0}},
            objective={"x": 1.0},
            lower_bounds={"x": 0.0},
            rhs={"lower": rhs},
            sense={"lower": ">="},
            variable_types={"x": variable_type},
        )

        result = solver.solve(model)

        assert result.status is SolverStatus.OPTIMAL
        assert result.values.get("x") == pytest.approx(expected)
        if variable_type == "continuous":
            assert result.dual_values is not None
        else:
            assert result.dual_values is None
        solver.cleanup()

    @pytest.mark.parametrize(
        ("sense", "rhs", "expected"),
        [
            ("<", 4.0, 0.0),
            ("<=", 4.0, 0.0),
            ("=<", 4.0, 0.0),
            (">", -1.0, 0.0),
            (">=", -1.0, 0.0),
            ("=>", -1.0, 0.0),
            ("=", 2.0, 2.0),
            ("==", 2.0, 2.0),
        ],
    )
    def test_solve_linear_triad_supports_sense_aliases(
        self,
        sense: str,
        rhs: float,
        expected: float,
    ) -> None:
        """约束方向别名均正确物化。"""
        solver = GurobiLinearSolver()
        model = LinearTriadModel(
            variables=["x"],
            objective={"x": 1.0},
            constraints={"c1": {"x": 1.0}},
            rhs={"c1": rhs},
            sense={"c1": sense},
            lower_bounds={"x": 0.0},
            upper_bounds={"x": 10.0},
        )

        result = solver.solve(model)

        assert result.status is SolverStatus.OPTIMAL
        assert result.values.get("x") == pytest.approx(expected)
        solver.cleanup()

    @pytest.mark.parametrize(
        "model",
        [
            pytest.param(LinearTriadModel(), id="no-variable"),
            pytest.param(
                LinearTriadModel(variables=["x", "x"]),
                id="duplicate-variable",
            ),
            pytest.param(
                LinearTriadModel(variables=["x"], objective={"x": float("nan")}),
                id="nan-objective",
            ),
            pytest.param(
                LinearTriadModel(variables=["x"], objective={"x": float("inf")}),
                id="infinite-objective",
            ),
            pytest.param(
                LinearTriadModel(variables=["x"], lower_bounds={"x": float("nan")}),
                id="nan-lower-bound",
            ),
            pytest.param(
                LinearTriadModel(
                    variables=["x"],
                    lower_bounds={"x": 2.0},
                    upper_bounds={"x": 1.0},
                ),
                id="crossed-bounds",
            ),
            pytest.param(
                LinearTriadModel(
                    variables=["x"],
                    constraints={"c1": {"x": float("nan")}},
                    rhs={"c1": 1.0},
                ),
                id="nan-constraint-coefficient",
            ),
            pytest.param(
                LinearTriadModel(
                    variables=["x"],
                    constraints={"c1": {"x": 1.0}},
                    rhs={"c1": float("inf")},
                ),
                id="infinite-rhs",
            ),
            pytest.param(
                LinearTriadModel(
                    variables=["x"],
                    constraints={"c1": {"x": 1.0}},
                    rhs={"c1": 1.0},
                    sense={"c1": "!="},
                ),
                id="unsupported-sense",
            ),
            pytest.param(
                LinearTriadModel(
                    variables=["x"],
                    constraints={"": {"x": 1.0}},
                    rhs={"": 1.0},
                ),
                id="empty-constraint-name",
            ),
            pytest.param(
                LinearTriadModel(
                    variables=["x"],
                    variable_types={"x": "semi_integer"},
                ),
                id="unsupported-variable-type",
            ),
            pytest.param(
                LinearTriadModel(
                    variables=["x"],
                    variable_types={"x": "binary"},
                    upper_bounds={"x": 2.0},
                ),
                id="invalid-binary-bound",
            ),
            pytest.param(
                LinearTriadModel(
                    variables=["x"],
                    variable_types={"unknown": "binary"},
                ),
                id="unknown-typed-variable",
            ),
        ],
    )
    def test_solve_linear_triad_rejects_invalid_shape(
        self,
        model: LinearTriadModel,
    ) -> None:
        """线性三元组无效形状返回 ERROR。"""
        solver = GurobiLinearSolver()

        result = solver.solve(model)

        assert result.status is SolverStatus.ERROR
        solver.cleanup()

    def test_failed_rematerialization_preserves_previous_model(self) -> None:
        """物化失败不销毁上一模型。"""
        solver = GurobiLinearSolver()
        valid = LinearTriadModel(
            variables=["x"],
            objective={"x": 1.0},
            lower_bounds={"x": 0.0},
        )
        assert solver.solve(valid).status is SolverStatus.OPTIMAL
        previous = solver._model
        assert previous is not None

        invalid = LinearTriadModel(
            variables=["x"],
            objective={"x": float("nan")},
        )
        result = solver.solve(invalid)

        assert result.status is SolverStatus.ERROR
        assert solver._model is previous
        assert previous.NumVars == 1
        solver.cleanup()

    def test_solve_rejects_unknown_model(self) -> None:
        """未知模型类型返回 ERROR。"""
        solver = GurobiLinearSolver()

        result = solver.solve(object())

        assert result.status is SolverStatus.ERROR
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
