"""Test variable types — 测试变量类型。"""

from __future__ import annotations

from ospf_python.core.variable.any_variable import AnyVariable
from ospf_python.core.variable.type import VariableType
from ospf_python.core.variable.variable_range import VariableRange


def test_continuous_variable() -> None:
    """Test continuous variable creation."""
    x = AnyVariable(
        name="x",
        index=0,
        type=VariableType.CONTINUOUS,
        bounds=VariableRange(lower=0.0, upper=10.0),
    )
    assert x.name == "x"
    assert x.type == VariableType.CONTINUOUS


def test_integer_variable() -> None:
    """Test integer variable creation."""
    y = AnyVariable(
        name="y",
        index=1,
        type=VariableType.INTEGER,
        bounds=VariableRange(lower=0, upper=100),
    )
    assert y.name == "y"
    assert y.type == VariableType.INTEGER


def test_binary_variable() -> None:
    """Test binary variable creation."""
    z = AnyVariable(
        name="z",
        index=2,
        type=VariableType.BINARY,
    )
    assert z.name == "z"
    assert z.type == VariableType.BINARY
