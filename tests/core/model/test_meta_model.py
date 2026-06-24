"""MetaModel 测试。

测试元模型的变量、约束和目标函数注册。
Tests MetaModel variable, constraint, and objective registration.
"""

from __future__ import annotations

from ospf_python.core.model.basic.registration_status import (
    RegistrationStatus,
)
from ospf_python.core.model.mechanism.meta_model import MetaModel


class TestMetaModelRegistration:
    """注册测试 / Registration tests."""

    def test_register_variable(self) -> None:
        """注册变量。/ Register a variable."""
        m = MetaModel()
        status = m.register_variable("x", "var_obj")
        assert status == RegistrationStatus.REGISTERED
        assert m.find_variable("x") == "var_obj"

    def test_register_variable_duplicate(self) -> None:
        """重复注册返回 ALREADY_EXISTS。/ Duplicate returns ALREADY_EXISTS."""
        m = MetaModel()
        m.register_variable("x", "v1")
        status = m.register_variable("x", "v2")
        assert status == RegistrationStatus.ALREADY_EXISTS

    def test_register_constraint(self) -> None:
        """注册约束。/ Register a constraint."""
        m = MetaModel()
        status = m.register_constraint("c1", "con_obj")
        assert status == RegistrationStatus.REGISTERED

    def test_register_objective(self) -> None:
        """注册目标函数。/ Register an objective."""
        m = MetaModel()
        status = m.register_objective("obj1", "obj_obj")
        assert status == RegistrationStatus.REGISTERED


class TestMetaModelQuery:
    """查询测试 / Query tests."""

    def test_find_missing_variable(self) -> None:
        """查找不存在的变量返回 None。/ Missing var returns None."""
        m = MetaModel()
        assert m.find_variable("no_such") is None

    def test_find_missing_constraint(self) -> None:
        """查找不存在的约束返回 None。/ Missing constraint returns None."""
        m = MetaModel()
        assert m.find_constraint("no_such") is None
