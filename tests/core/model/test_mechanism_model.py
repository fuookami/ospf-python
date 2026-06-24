"""MechanismModel 测试。

测试机制模型的创建、构建和验证。
Tests MechanismModel creation, build, and validation.
"""

from __future__ import annotations

from ospf_python.core.model.mechanism.basic_mechanism_model import (
    BasicMechanismModel,
)
from ospf_python.core.model.mechanism.mechanism_model import (
    MechanismModel,
)
from ospf_python.core.model.mechanism.mechanism_model_cut_support import (
    MechanismModelCutSupport,
)
from ospf_python.core.model.mechanism.mechanism_model_objective_support import (
    MechanismModelObjectiveSupport,
)


class TestMechanismModel:
    """机制模型测试 / Mechanism model tests."""

    def test_inherits_basic(self) -> None:
        """继承 BasicMechanismModel。/ Inherits BasicMechanismModel."""
        m = MechanismModel()
        assert isinstance(m, BasicMechanismModel)

    def test_build(self) -> None:
        """构建不抛异常。/ Build does not raise."""
        m = MechanismModel()
        m.build()

    def test_validate(self) -> None:
        """验证返回 True。/ Validate returns True."""
        m = MechanismModel()
        assert m.validate() is True


class TestBasicMechanismModel:
    """基础机制模型测试 / Basic mechanism model tests."""

    def test_register_variable(self) -> None:
        """注册变量。/ Register a variable."""
        m = BasicMechanismModel()
        m.register_variable("x")
        assert "x" in m.registered_variables

    def test_register_constraint(self) -> None:
        """注册约束。/ Register a constraint."""
        m = BasicMechanismModel()
        m.register_constraint("c1")
        assert len(m.registered_constraints) == 1


class TestMechanismModelCutSupport:
    """切割支持测试 / Cut support tests."""

    def test_add_cut(self) -> None:
        """添加切割平面。/ Add a cut."""
        s = MechanismModelCutSupport()
        s.add_cut("cut1")
        assert s.cut_count == 1

    def test_clear_cuts(self) -> None:
        """清除切割。/ Clear cuts."""
        s = MechanismModelCutSupport()
        s.add_cut("cut1")
        s.clear_cuts()
        assert s.cut_count == 0


class TestMechanismModelObjectiveSupport:
    """目标函数支持测试 / Objective support tests."""

    def test_add_objective(self) -> None:
        """添加目标函数。/ Add an objective."""
        s = MechanismModelObjectiveSupport()
        s.add_objective("obj1")
        assert s.objective_count == 1

    def test_clear_objectives(self) -> None:
        """清除目标函数。/ Clear objectives."""
        s = MechanismModelObjectiveSupport()
        s.add_objective("obj1")
        s.clear_objectives()
        assert s.objective_count == 0

    def test_default_minimize(self) -> None:
        """默认为最小化。/ Default is minimize."""
        s = MechanismModelObjectiveSupport()
        assert s.minimize is True
