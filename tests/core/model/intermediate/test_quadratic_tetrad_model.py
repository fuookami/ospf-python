"""QuadraticTetradModel 测试。

测试二次四元组中间模型的创建和字段。
Tests QuadraticTetradModel creation and fields.
"""

from __future__ import annotations

from ospf_python.core.model.intermediate.quadratic_tetrad_model import (
    QuadraticTetradModel,
)


class TestQuadraticTetradModel:
    """二次四元组模型测试 / QuadraticTetradModel tests."""

    def test_default_name(self) -> None:
        """默认名称为空。/ Default name is empty."""
        m = QuadraticTetradModel()
        assert m.name == ""

    def test_custom_name(self) -> None:
        """自定义名称。/ Custom name."""
        m = QuadraticTetradModel(name="qp_model")
        assert m.name == "qp_model"

    def test_default_collections_empty(self) -> None:
        """默认集合为空。/ Default collections are empty."""
        m = QuadraticTetradModel()
        assert m.variables == []
        assert m.linear_constraints == {}
        assert m.quadratic_constraints == {}
        assert m.objective == {}
        assert m.lower_bounds == {}
        assert m.upper_bounds == {}
        assert m.rhs == {}
        assert m.sense == {}

    def test_add_linear_constraint(self) -> None:
        """添加线性约束。/ Add linear constraint."""
        m = QuadraticTetradModel()
        m.linear_constraints["c1"] = {"x1": 1.0}
        assert "c1" in m.linear_constraints

    def test_add_quadratic_constraint(self) -> None:
        """添加二次约束。/ Add quadratic constraint."""
        m = QuadraticTetradModel()
        m.quadratic_constraints["qc1"] = {
            ("x1", "x1"): 1.0,
        }
        assert "qc1" in m.quadratic_constraints
        assert m.quadratic_constraints["qc1"][("x1", "x1")] == 1.0

    def test_set_bounds(self) -> None:
        """设置边界。/ Set bounds."""
        m = QuadraticTetradModel()
        m.lower_bounds["x1"] = 0.0
        m.upper_bounds["x1"] = 10.0
        assert m.lower_bounds["x1"] == 0.0
        assert m.upper_bounds["x1"] == 10.0

    def test_set_objective(self) -> None:
        """设置目标函数。/ Set objective."""
        m = QuadraticTetradModel()
        m.objective["x1"] = 3.0
        assert m.objective["x1"] == 3.0

    def test_set_rhs_and_sense(self) -> None:
        """设置右端项和方向。/ Set RHS and sense."""
        m = QuadraticTetradModel()
        m.rhs["c1"] = 10.0
        m.sense["c1"] = "<="
        assert m.rhs["c1"] == 10.0
        assert m.sense["c1"] == "<="
