"""BasicMechanismModel 测试。

测试基础机制模型的创建和注册方法。
Tests BasicMechanismModel creation and registration methods.
"""

from __future__ import annotations

from ospf_python.core.model.mechanism.basic_mechanism_model import (
    BasicMechanismModel,
)


class TestBasicMechanismModel:
    """基础机制模型测试 / BasicMechanismModel tests."""

    def test_default_name(self) -> None:
        """默认名称为空。/ Default name is empty."""
        m = BasicMechanismModel()
        assert m.name == ""

    def test_custom_name(self) -> None:
        """自定义名称。/ Custom name."""
        m = BasicMechanismModel(name="mech")
        assert m.name == "mech"

    def test_default_collections_empty(self) -> None:
        """默认集合为空。/ Default collections are empty."""
        m = BasicMechanismModel()
        assert m.registered_constraints == []
        assert m.registered_variables == set()

    def test_register_variable(self) -> None:
        """注册变量。/ Register variable."""
        m = BasicMechanismModel()
        m.register_variable("x1")
        assert "x1" in m.registered_variables

    def test_register_variable_duplicate(self) -> None:
        """重复注册变量无副作用。/ Duplicate registration is idempotent."""
        m = BasicMechanismModel()
        m.register_variable("x1")
        m.register_variable("x1")
        assert len(m.registered_variables) == 1

    def test_register_constraint(self) -> None:
        """注册约束。/ Register constraint."""
        m = BasicMechanismModel()
        m.register_constraint("c1")
        assert "c1" in m.registered_constraints

    def test_register_multiple_constraints(self) -> None:
        """注册多个约束。/ Register multiple constraints."""
        m = BasicMechanismModel()
        m.register_constraint("c1")
        m.register_constraint("c2")
        assert len(m.registered_constraints) == 2

    def test_register_mixed(self) -> None:
        """同时注册变量和约束。/ Register both variables and constraints."""
        m = BasicMechanismModel()
        m.register_variable("x1")
        m.register_constraint("c1")
        assert "x1" in m.registered_variables
        assert "c1" in m.registered_constraints
