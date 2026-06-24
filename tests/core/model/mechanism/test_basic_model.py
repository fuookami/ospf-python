"""BasicModel 测试。

测试基础模型的创建和操作方法。
Tests BasicModel creation and operation methods.
"""

from __future__ import annotations

from ospf_python.core.model.mechanism.basic_model import BasicModel


class TestBasicModel:
    """基础模型测试 / BasicModel tests."""

    def test_default_name(self) -> None:
        """默认名称为空。/ Default name is empty."""
        m = BasicModel()
        assert m.name == ""

    def test_custom_name(self) -> None:
        """自定义名称。/ Custom name."""
        m = BasicModel(name="model")
        assert m.name == "model"

    def test_default_collections_empty(self) -> None:
        """默认集合为空。/ Default collections are empty."""
        m = BasicModel()
        assert m.constraints == []
        assert m.objectives == []

    def test_add_constraint(self) -> None:
        """添加约束。/ Add constraint."""
        m = BasicModel()
        m.add_constraint("c1")
        assert "c1" in m.constraints

    def test_add_multiple_constraints(self) -> None:
        """添加多个约束。/ Add multiple constraints."""
        m = BasicModel()
        m.add_constraint("c1")
        m.add_constraint("c2")
        assert len(m.constraints) == 2

    def test_add_objective(self) -> None:
        """添加目标函数。/ Add objective."""
        m = BasicModel()
        m.add_objective("obj1")
        assert "obj1" in m.objectives

    def test_add_multiple_objectives(self) -> None:
        """添加多个目标函数。/ Add multiple objectives."""
        m = BasicModel()
        m.add_objective("obj1")
        m.add_objective("obj2")
        assert len(m.objectives) == 2

    def test_add_mixed(self) -> None:
        """同时添加约束和目标。/ Add both constraints and objectives."""
        m = BasicModel()
        m.add_constraint("c1")
        m.add_objective("obj1")
        assert len(m.constraints) == 1
        assert len(m.objectives) == 1
