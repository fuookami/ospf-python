"""COPT 求解器测试 / COPT solver tests.

使用 pytest.importorskip 在 coptpy 未安装时优雅跳过。
Uses pytest.importorskip to skip gracefully when coptpy
is not installed.
"""

from __future__ import annotations

import pytest

coptpy = pytest.importorskip("coptpy")

from ospf_python.core.solver.config.copt_solver_config import (
    CoptSolverConfig,  # noqa: E402
)
from ospf_python.core.solver.copt.copt_constraint import CoptConstraint  # noqa: E402
from ospf_python.core.solver.copt.copt_linear_solver import (
    CoptLinearSolver,  # noqa: E402
)
from ospf_python.core.solver.copt.copt_variable import CoptVariable  # noqa: E402


def _copt_available() -> bool:
    """检查 COPT 许可证是否可用 / Check if COPT license is available."""
    try:
        m = coptpy.Model("test")
        m.dispose()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _copt_available(), reason="COPT license not available")
class TestCoptLinearSolver:
    """COPT 线性求解器测试 / COPT linear solver tests."""

    def test_create_copt_model(self) -> None:
        """创建 coptpy 模型 / Create coptpy model."""
        solver = CoptLinearSolver()
        model = solver._get_or_create_model()
        assert model is not None
        solver.cleanup()

    def test_solve_simple_lp(self) -> None:
        """求解简单 LP / Solve a simple LP."""
        solver = CoptLinearSolver()
        m = solver._get_or_create_model()
        x = m.addVar(name="x", lb=0.0)
        y = m.addVar(name="y", lb=0.0)
        m.setObjective(x + 2 * y, sense=coptpy.COPT.MINIMIZE)
        m.addConstr(x + y <= 10, name="c1")
        m.solve()
        assert m.status == coptpy.COPT.OPTIMAL
        solver.cleanup()


class TestCoptSolverConfig:
    """COPT 配置测试 / COPT config tests."""

    def test_config_creation(self) -> None:
        """创建配置 / Create config."""
        config = CoptSolverConfig()
        assert config is not None


class TestCoptTypes:
    """COPT 类型测试 / COPT type tests."""

    def test_variable_type(self) -> None:
        """变量类型 / Variable type."""
        assert CoptVariable is not None

    def test_constraint_type(self) -> None:
        """约束类型 / Constraint type."""
        assert CoptConstraint is not None
