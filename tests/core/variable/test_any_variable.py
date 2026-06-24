"""AnyVariable 测试。

测试通用变量的创建、类型和属性。
Tests AnyVariable creation, type, and attributes.
"""

from __future__ import annotations

import pytest

from ospf_python.core.variable.abstract_variable_item import (
    AbstractVariableItem,
)
from ospf_python.core.variable.any_variable import AnyVariable
from ospf_python.core.variable.type import VariableType


class TestAnyVariableCreation:
    """创建测试 / Creation tests."""

    def test_create_continuous(self) -> None:
        """创建连续变量。/ Create continuous variable."""
        v = AnyVariable.continuous(
            name="x",
            index=0,
            lower=0.0,
            upper=10.0,
        )
        assert v.name == "x"
        assert v.index == 0
        assert v.type is VariableType.CONTINUOUS

    def test_create_integer(self) -> None:
        """创建整数变量。/ Create integer variable."""
        v = AnyVariable.integer(name="y", index=1)
        assert v.type is VariableType.INTEGER

    def test_create_binary(self) -> None:
        """创建二元变量。/ Create binary variable."""
        v = AnyVariable.binary(name="b", index=2)
        assert v.type is VariableType.BINARY
        assert v.bounds.lower == 0.0
        assert v.bounds.upper == 1.0

    def test_is_abstract_subclass(self) -> None:
        """是 AbstractVariableItem 子类。/ Is subclass."""
        v = AnyVariable.continuous(name="x", index=0)
        assert isinstance(v, AbstractVariableItem)


class TestAnyVariableAttributes:
    """属性测试 / Attribute tests."""

    def test_str_format(self) -> None:
        """字符串格式正确。/ String format correct."""
        v = AnyVariable(
            name="x",
            type=VariableType.CONTINUOUS,
            index=5,
        )
        assert str(v) == "x[5](continuous)"

    def test_is_frozen(self) -> None:
        """变量不可变。/ Variable is frozen."""
        v = AnyVariable.continuous(name="x", index=0)
        with pytest.raises(AttributeError):
            v.name = "changed"  # type: ignore[misc]

    def test_default_bounds(self) -> None:
        """默认范围为无界。/ Default bounds unbounded."""
        v = AnyVariable.continuous(name="x", index=0)
        assert v.bounds.lower == float("-inf")
        assert v.bounds.upper == float("inf")
