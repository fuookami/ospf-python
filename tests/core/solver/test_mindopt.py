"""MindOPT 求解器测试 / MindOPT solver tests.

使用 pytest.importorskip 在 mindoptpy 未安装时优雅跳过。
Uses pytest.importorskip to skip gracefully when mindoptpy
is not installed.
"""

from __future__ import annotations

import pytest

mindoptpy = pytest.importorskip("mindoptpy")

from ospf_python.core.solver.mindopt.mindopt_constraint import (
    MindOPTConstraint,  # noqa: E402
)
from ospf_python.core.solver.mindopt.mindopt_linear_solver import (
    MindOPTLinearSolver,  # noqa: E402
)
from ospf_python.core.solver.mindopt.mindopt_variable import (
    MindOPTVariable,  # noqa: E402
)


def _mindopt_available() -> bool:
    """检查 MindOPT 许可证是否可用 / Check if MindOPT license is available."""
    try:
        m = mindoptpy.Model("test")
        m.dispose()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _mindopt_available(), reason="MindOPT license not available")
class TestMindOPTLinearSolver:
    """MindOPT 线性求解器测试 / MindOPT linear solver tests."""

    def test_create_mindopt_model(self) -> None:
        """创建 mindoptpy 模型 / Create mindoptpy model."""
        solver = MindOPTLinearSolver()
        model = solver._get_or_create_model()
        assert model is not None
        solver.cleanup()


class TestMindOPTTypes:
    """MindOPT 类型测试 / MindOPT type tests."""

    def test_variable_type(self) -> None:
        """变量类型 / Variable type."""
        assert MindOPTVariable is not None

    def test_constraint_type(self) -> None:
        """约束类型 / Constraint type."""
        assert MindOPTConstraint is not None
