"""Test MetaModel creation and registration — 测试 MetaModel 创建与注册。"""

from __future__ import annotations

from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.variable.any_variable import AnyVariable
from ospf_python.core.variable.type import VariableType


def test_meta_model_creation() -> None:
    """Test creating a MetaModel."""
    model = MetaModel(name="test")
    assert model.name == "test"
    assert len(model.variables) == 0


def test_register_variable() -> None:
    """Test registering a variable."""
    model = MetaModel(name="test")
    x = AnyVariable(name="x", index=0, type=VariableType.CONTINUOUS)
    model.register_variable("x", x)
    assert len(model.variables) == 1


def test_register_constraint() -> None:
    """Test registering a constraint."""
    model = MetaModel(name="test")
    model.register_constraint("c1", object())
    assert len(model.constraints) == 1
