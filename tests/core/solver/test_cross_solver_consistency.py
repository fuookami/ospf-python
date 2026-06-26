"""跨求解器一致性测试 / Cross-solver consistency tests.

构建 LP 和 MILP 实例，经框架 Solver 接口用 4 个求解器各解，
断言目标值/状态一致，验证迁移求解正确性。

Build LP and MILP instances, solve via framework Solver interface
using 4 solvers, assert objective/status consistency to verify
migration solve correctness.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ospf_python.core.solver.copt.copt_linear_solver import CoptLinearSolver
from ospf_python.core.solver.mindopt.mindopt_linear_solver import (
    MindOPTLinearSolver,
)
from ospf_python.core.solver.output.solver_status import SolverStatus

if TYPE_CHECKING:
    from ospf_python.core.solver.linear_solver import LinearSolver
    from ospf_python.core.solver.output.solver_output import SolverOutput


# ============================================================
# 求解器工厂 / Solver factories
# ============================================================


def _create_gurobi_solver() -> LinearSolver:
    """创建 Gurobi 线性求解器 / Create Gurobi linear solver."""
    from ospf_python.core.solver.gurobi.gurobi_linear_solver import (
        GurobiLinearSolver,
    )

    return GurobiLinearSolver()


def _create_scip_solver() -> LinearSolver:
    """创建 SCIP 线性求解器 / Create SCIP linear solver."""
    from ospf_python.core.solver.scip.scip_linear_solver import (
        ScipLinearSolver,
    )

    return ScipLinearSolver()


def _create_copt_solver() -> LinearSolver | None:
    """创建 COPT 线性求解器 / Create COPT linear solver.

    Returns:
        求解器实例或 None（许可证不可用时）/ Solver instance or None (when license unavailable).
    """
    from ospf_python.core.solver.copt.copt_linear_solver import (
        CoptLinearSolver,
    )

    solver = CoptLinearSolver()
    try:
        solver._get_or_create_model()
        return solver
    except (AssertionError, Exception):
        solver.cleanup()
        return None


def _create_mindopt_solver() -> LinearSolver | None:
    """创建 MindOPT 线性求解器 / Create MindOPT linear solver.

    Returns:
        求解器实例或 None（许可证不可用时）/ Solver instance or None (when license unavailable).
    """
    from ospf_python.core.solver.mindopt.mindopt_linear_solver import (
        MindOPTLinearSolver,
    )

    solver = MindOPTLinearSolver()
    try:
        solver._get_or_create_model()
        return solver
    except Exception:
        solver.cleanup()
        return None


# ============================================================
# LP 构建器 / LP builders
# ============================================================


def _build_gurobi_lp(solver: LinearSolver) -> SolverOutput:
    """用 Gurobi 构建并求解 LP / Build and solve LP with Gurobi.

    min  x + 2y
    s.t. x + y <= 10
         x, y >= 0
    """
    from gurobipy import GRB

    m = solver._get_or_create_model()
    x = m.addVar(lb=0.0, name="x", vtype=GRB.CONTINUOUS)
    y = m.addVar(lb=0.0, name="y", vtype=GRB.CONTINUOUS)
    m.setObjective(x + 2 * y, GRB.MINIMIZE)
    m.addConstr(x + y <= 10, name="c1")
    m.update()

    # 传递一个带有 objective_sense 的包装对象
    # Pass a wrapper with objective_sense
    class _Sense:
        objective_sense = "min"

    return solver.solve(_Sense())


def _build_scip_lp(solver: LinearSolver) -> SolverOutput:
    """用 SCIP 构建并求解 LP / Build and solve LP with SCIP."""
    m = solver._get_or_create_model()
    x = m.addVar("x", lb=0.0, vtype="CONTINUOUS")
    y = m.addVar("y", lb=0.0, vtype="CONTINUOUS")
    m.setObjective(x + 2 * y, "minimize")
    m.addCons(x + y <= 10, name="c1")

    class _Sense:
        objective_sense = "min"

    return solver.solve(_Sense())


def _build_copt_lp(solver: LinearSolver) -> SolverOutput:
    """用 COPT 构建并求解 LP / Build and solve LP with COPT."""
    import coptpy as cp

    m = solver._get_or_create_model()
    x = m.addVar(lb=0.0, name="x", vtype=cp.Continuous)
    y = m.addVar(lb=0.0, name="y", vtype=cp.Continuous)
    m.setObjective(x + 2 * y)
    m.addConstr(x + y <= 10, name="c1")

    class _Sense:
        objective_sense = "min"

    return solver.solve(_Sense())


def _build_mindopt_lp(solver: LinearSolver) -> SolverOutput:
    """用 MindOPT 构建并求解 LP / Build and solve LP with MindOPT."""
    m = solver._get_or_create_model()
    x = m.addVar(lb=0.0, name="x", vtype="C")
    y = m.addVar(lb=0.0, name="y", vtype="C")
    m.setObjective(x + 2 * y)
    m.addConstr(x + y <= 10, name="c1")

    class _Sense:
        objective_sense = "min"

    return solver.solve(_Sense())


# ============================================================
# MILP 构建器 / MILP builders
# ============================================================


def _build_gurobi_milp(solver: LinearSolver) -> SolverOutput:
    """用 Gurobi 构建并求解 MILP / Build and solve MILP with Gurobi.

    min  x + y
    s.t. x + y >= 5
         x integer, 0 <= x <= 10
         y >= 0
    """
    from gurobipy import GRB

    m = solver._get_or_create_model()
    x = m.addVar(lb=0.0, ub=10.0, name="x", vtype=GRB.INTEGER)
    y = m.addVar(lb=0.0, name="y", vtype=GRB.CONTINUOUS)
    m.setObjective(x + y, GRB.MINIMIZE)
    m.addConstr(x + y >= 5, name="c1")
    m.update()

    class _Sense:
        objective_sense = "min"

    return solver.solve(_Sense())


def _build_scip_milp(solver: LinearSolver) -> SolverOutput:
    """用 SCIP 构建并求解 MILP / Build and solve MILP with SCIP."""
    m = solver._get_or_create_model()
    x = m.addVar("x", lb=0.0, ub=10.0, vtype="INTEGER")
    y = m.addVar("y", lb=0.0, vtype="CONTINUOUS")
    m.setObjective(x + y, "minimize")
    m.addCons(x + y >= 5, name="c1")

    class _Sense:
        objective_sense = "min"

    return solver.solve(_Sense())


def _build_copt_milp(solver: LinearSolver) -> SolverOutput:
    """用 COPT 构建并求解 MILP / Build and solve MILP with COPT."""
    import coptpy as cp

    m = solver._get_or_create_model()
    x = m.addVar(lb=0.0, ub=10.0, name="x", vtype=cp.Integer)
    y = m.addVar(lb=0.0, name="y", vtype=cp.Continuous)
    m.setObjective(x + y)
    m.addConstr(x + y >= 5, name="c1")

    class _Sense:
        objective_sense = "min"

    return solver.solve(_Sense())


def _build_mindopt_milp(solver: LinearSolver) -> SolverOutput:
    """用 MindOPT 构建并求解 MILP / Build and solve MILP with MindOPT."""
    m = solver._get_or_create_model()
    x = m.addVar(lb=0.0, ub=10.0, name="x", vtype="I")
    y = m.addVar(lb=0.0, name="y", vtype="C")
    m.setObjective(x + y)
    m.addConstr(x + y >= 5, name="c1")

    class _Sense:
        objective_sense = "min"

    return solver.solve(_Sense())


# ============================================================
# 求解器注册表 / Solver registry
# ============================================================

# 每项：(名称, 库名, 创建器, LP构建器, MILP构建器)
# Each entry: (name, lib_name, creator, lp_builder, milp_builder)
SOLVER_REGISTRY: list[
    tuple[
        str,
        str,
        type[LinearSolver],
        type[LinearSolver],
    ]
] = []

# 动态注册可用求解器 / Dynamically register available solvers
_SOLVER_DEFS: list[
    tuple[str, str, type[LinearSolver] | None, type[LinearSolver] | None]
] = []


def _check_solver_available(solver_name: str) -> bool:
    """检查求解器是否真正可用（含许可证）/ Check if solver is truly available (including license).

    Args:
        solver_name: 求解器名称 / Solver name.

    Returns:
        是否可用 / Whether available.
    """
    if solver_name == "gurobi":
        try:
            import gurobipy

            m = gurobipy.Model()
            m.dispose()
            return True
        except Exception:
            return False
    elif solver_name == "scip":
        try:
            from pyscipopt import Model

            m = Model()
            m.freeProb()
            return True
        except Exception:
            return False
    elif solver_name == "copt":
        try:
            import coptpy

            m = coptpy.Model()
            m.dispose()
            return True
        except Exception:
            return False
    elif solver_name == "mindopt":
        try:
            import mindoptpy

            m = mindoptpy.Model()
            m.dispose()
            return True
        except Exception:
            return False
    return False


# 可用求解器列表（含许可证检查）/ Available solvers (with license check)
AVAILABLE_SOLVER_NAMES = [
    name
    for name in ["gurobi", "scip", "copt", "mindopt"]
    if _check_solver_available(name)
]


# ============================================================
# LP 一致性测试 / LP consistency tests
# ============================================================


@pytest.mark.benchmark
class TestLPConsistency:
    """LP 跨求解器一致性 / LP cross-solver consistency.

    验证可用求解器对同一 LP 实例的目标值一致。
    Verify objective consistency across available solvers for
    the same LP instance.
    """

    @pytest.mark.parametrize(
        "solver_name",
        ["gurobi", "scip", "copt", "mindopt"],
    )
    def test_lp_objective(self, solver_name: str) -> None:
        """LP 目标值测试 / LP objective test.

        min  x + 2y = 0 (at x=0, y=0)
        s.t. x + y <= 10
             x, y >= 0

        Args:
            solver_name: 求解器名称 / Solver name.
        """
        if not _check_solver_available(solver_name):
            pytest.skip(f"{solver_name} license not available")

        builder = {
            "gurobi": _build_gurobi_lp,
            "scip": _build_scip_lp,
            "copt": _build_copt_lp,
            "mindopt": _build_mindopt_lp,
        }[solver_name]

        solver = {
            "gurobi": _create_gurobi_solver,
            "scip": _create_scip_solver,
            "copt": lambda: CoptLinearSolver(),
            "mindopt": lambda: MindOPTLinearSolver(),
        }[solver_name]()

        try:
            result = builder(solver)
            assert result.status is SolverStatus.OPTIMAL, (
                f"{solver_name}: expected OPTIMAL, got {result.status}"
            )
            assert result.objective is not None
            # LP 最优解应为 0（x=0, y=0）
            assert abs(result.objective) < 1e-6, (
                f"{solver_name}: expected objective ~0, got {result.objective}"
            )
        finally:
            solver.cleanup()

    def test_lp_all_solvers_agree(self) -> None:
        """LP 所有求解器一致 / LP all solvers agree."""
        if len(AVAILABLE_SOLVER_NAMES) < 2:
            pytest.skip("Need at least 2 solvers for consistency test")

        results: dict[str, SolverOutput] = {}

        for solver_name in AVAILABLE_SOLVER_NAMES:
            builder = {
                "gurobi": _build_gurobi_lp,
                "scip": _build_scip_lp,
                "copt": _build_copt_lp,
                "mindopt": _build_mindopt_lp,
            }[solver_name]

            solver = {
                "gurobi": _create_gurobi_solver,
                "scip": _create_scip_solver,
                "copt": lambda: CoptLinearSolver(),
                "mindopt": lambda: MindOPTLinearSolver(),
            }[solver_name]()

            try:
                results[solver_name] = builder(solver)
            finally:
                solver.cleanup()

        for name, result in results.items():
            assert result.status is SolverStatus.OPTIMAL, (
                f"{name}: expected OPTIMAL, got {result.status}"
            )

        objectives = {name: result.objective for name, result in results.items()}
        ref_name = next(iter(objectives))
        ref_obj = objectives[ref_name]

        for name, obj in objectives.items():
            if name == ref_name:
                continue
            assert abs(obj - ref_obj) < 1e-6, (
                f"LP objective mismatch: {ref_name}={ref_obj}, "
                f"{name}={obj}, diff={abs(obj - ref_obj)}"
            )


# ============================================================
# MILP 一致性测试 / MILP consistency tests
# ============================================================


@pytest.mark.benchmark
class TestMILPConsistency:
    """MILP 跨求解器一致性 / MILP cross-solver consistency.

    验证可用求解器对同一 MILP 实例的目标值一致。
    Verify objective consistency across available solvers for
    the same MILP instance.
    """

    @pytest.mark.parametrize(
        "solver_name",
        ["gurobi", "scip", "copt", "mindopt"],
    )
    def test_milp_objective(self, solver_name: str) -> None:
        """MILP 目标值测试 / MILP objective test.

        min  x + y
        s.t. x + y >= 5
             x integer, 0 <= x <= 10
             y >= 0

        Args:
            solver_name: 求解器名称 / Solver name.
        """
        if not _check_solver_available(solver_name):
            pytest.skip(f"{solver_name} license not available")

        builder = {
            "gurobi": _build_gurobi_milp,
            "scip": _build_scip_milp,
            "copt": _build_copt_milp,
            "mindopt": _build_mindopt_milp,
        }[solver_name]

        solver = {
            "gurobi": _create_gurobi_solver,
            "scip": _create_scip_solver,
            "copt": lambda: CoptLinearSolver(),
            "mindopt": lambda: MindOPTLinearSolver(),
        }[solver_name]()

        try:
            result = builder(solver)
            assert result.status is SolverStatus.OPTIMAL, (
                f"{solver_name}: expected OPTIMAL, got {result.status}"
            )
            assert result.objective is not None
            # MILP 最优解应为 5（x=5, y=0）
            assert abs(result.objective - 5.0) < 1e-9, (
                f"{solver_name}: expected objective ~5, got {result.objective}"
            )
        finally:
            solver.cleanup()

    def test_milp_all_solvers_agree(self) -> None:
        """MILP 所有求解器一致 / MILP all solvers agree."""
        if len(AVAILABLE_SOLVER_NAMES) < 2:
            pytest.skip("Need at least 2 solvers for consistency test")

        results: dict[str, SolverOutput] = {}

        for solver_name in AVAILABLE_SOLVER_NAMES:
            builder = {
                "gurobi": _build_gurobi_milp,
                "scip": _build_scip_milp,
                "copt": _build_copt_milp,
                "mindopt": _build_mindopt_milp,
            }[solver_name]

            solver = {
                "gurobi": _create_gurobi_solver,
                "scip": _create_scip_solver,
                "copt": lambda: CoptLinearSolver(),
                "mindopt": lambda: MindOPTLinearSolver(),
            }[solver_name]()

            try:
                results[solver_name] = builder(solver)
            finally:
                solver.cleanup()

        for name, result in results.items():
            assert result.status is SolverStatus.OPTIMAL, (
                f"{name}: expected OPTIMAL, got {result.status}"
            )

        objectives = {name: result.objective for name, result in results.items()}
        ref_name = next(iter(objectives))
        ref_obj = objectives[ref_name]

        for name, obj in objectives.items():
            if name == ref_name:
                continue
            assert abs(obj - ref_obj) < 1e-9, (
                f"MILP objective mismatch: {ref_name}={ref_obj}, "
                f"{name}={obj}, diff={abs(obj - ref_obj)}"
            )

        for name, obj in objectives.items():
            assert abs(obj - 5.0) < 1e-9, f"{name}: expected objective 5, got {obj}"
