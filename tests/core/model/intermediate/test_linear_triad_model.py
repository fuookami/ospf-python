"""LinearTriadModel 测试。

测试线性三元组中间模型的创建和字段。
Tests LinearTriadModel creation and fields.
"""

from __future__ import annotations

from ospf_python.core.model.intermediate.linear_triad_model import (
    LinearTriadModel,
)


class TestLinearTriadModel:
    """线性三元组模型测试 / LinearTriadModel tests."""

    def test_default_name(self) -> None:
        """默认名称为空。/ Default name is empty."""
        m = LinearTriadModel()
        assert m.name == ""

    def test_custom_name(self) -> None:
        """自定义名称。/ Custom name."""
        m = LinearTriadModel(name="test_model")
        assert m.name == "test_model"

    def test_default_collections_empty(self) -> None:
        """默认集合为空。/ Default collections are empty."""
        m = LinearTriadModel()
        assert m.variables == []
        assert m.constraints == {}
        assert m.objective == {}
        assert m.lower_bounds == {}
        assert m.upper_bounds == {}
        assert m.rhs == {}
        assert m.sense == {}

    def test_add_variable(self) -> None:
        """添加变量。/ Add variable."""
        m = LinearTriadModel()
        m.variables.append("x1")
        assert "x1" in m.variables

    def test_add_constraint(self) -> None:
        """添加约束。/ Add constraint."""
        m = LinearTriadModel()
        m.constraints["c1"] = {"x1": 1.0, "x2": 2.0}
        assert "c1" in m.constraints
        assert m.constraints["c1"]["x1"] == 1.0

    def test_set_bounds(self) -> None:
        """设置边界。/ Set bounds."""
        m = LinearTriadModel()
        m.lower_bounds["x1"] = 0.0
        m.upper_bounds["x1"] = 10.0
        assert m.lower_bounds["x1"] == 0.0
        assert m.upper_bounds["x1"] == 10.0

    def test_set_objective(self) -> None:
        """设置目标函数。/ Set objective."""
        m = LinearTriadModel()
        m.objective["x1"] = 3.0
        m.objective["x2"] = 5.0
        assert m.objective["x1"] == 3.0

    def test_set_rhs_and_sense(self) -> None:
        """设置右端项和方向。/ Set RHS and sense."""
        m = LinearTriadModel()
        m.rhs["c1"] = 10.0
        m.sense["c1"] = "<="
        assert m.rhs["c1"] == 10.0
        assert m.sense["c1"] == "<="
