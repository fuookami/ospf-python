"""TriadDualSolverSupport 测试。

测试三元组对偶求解器支持的提取方法。
Tests TriadDualSolverSupport extraction methods.
"""

from __future__ import annotations

from ospf_python.core.model.intermediate.linear_triad_model import (
    LinearTriadModel,
)
from ospf_python.core.model.intermediate.triad_dual_solver_support import (
    TriadDualSolverSupport,
)


class TestTriadDualSolverSupport:
    """对偶求解器支持测试 / TriadDualSolverSupport tests."""

    def test_extract_dual_values_basic(self) -> None:
        """基本对偶值提取。/ Basic dual value extraction."""
        m = LinearTriadModel()
        m.constraints["c1"] = {"x1": 1.0}
        m.constraints["c2"] = {"x2": 1.0}
        dual = {"c1": 3.0, "c2": 5.0}
        result = TriadDualSolverSupport.extract_dual_values(m, dual)
        assert result["c1"] == 3.0
        assert result["c2"] == 5.0

    def test_extract_dual_values_missing(self) -> None:
        """缺失约束默认为 0。/ Missing constraint defaults to 0."""
        m = LinearTriadModel()
        m.constraints["c1"] = {"x1": 1.0}
        dual: dict[str, float] = {}
        result = TriadDualSolverSupport.extract_dual_values(m, dual)
        assert result["c1"] == 0.0

    def test_extract_dual_values_empty_model(self) -> None:
        """空模型返回空字典。/ Empty model returns empty dict."""
        m = LinearTriadModel()
        dual = {"c1": 1.0}
        result = TriadDualSolverSupport.extract_dual_values(m, dual)
        assert result == {}

    def test_extract_dual_values_extra_keys(self) -> None:
        """额外对偶键被忽略。/ Extra dual keys ignored."""
        m = LinearTriadModel()
        m.constraints["c1"] = {"x1": 1.0}
        dual = {"c1": 2.0, "extra": 99.0}
        result = TriadDualSolverSupport.extract_dual_values(m, dual)
        assert "extra" not in result
        assert len(result) == 1
