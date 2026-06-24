"""VariableCombinationItem 测试。

测试组合变量项的创建、组件和工厂方法。
Tests VariableCombinationItem creation, components,
and factory methods.
"""

from __future__ import annotations

import pytest

from ospf_python.core.variable.abstract_variable_item import (
    AbstractVariableItem,
)
from ospf_python.core.variable.type import VariableType
from ospf_python.core.variable.variable_combination_item import (
    VariableCombinationItem,
)


class TestVariableCombinationItemCreation:
    """创建测试 / Creation tests."""

    def test_create_empty_combination(self) -> None:
        """创建空组合变量。/ Create empty combination."""
        v = VariableCombinationItem(
            name="c",
            type=VariableType.CONTINUOUS,
            index=0,
        )
        assert v.component_count == 0

    def test_create_with_components(self) -> None:
        """创建带组件的组合变量。/ Create with components."""
        v = VariableCombinationItem(
            name="c",
            type=VariableType.CONTINUOUS,
            index=0,
            component_indices=(1, 2, 3),
        )
        assert v.component_count == 3
        assert v.component_indices == (1, 2, 3)

    def test_is_abstract_subclass(self) -> None:
        """是 AbstractVariableItem 子类。/ Is subclass."""
        v = VariableCombinationItem(
            name="c",
            type=VariableType.CONTINUOUS,
            index=0,
        )
        assert isinstance(v, AbstractVariableItem)


class TestVariableCombinationItemComponents:
    """组件测试 / Component tests."""

    def test_has_component_true(self) -> None:
        """包含组件判断为真。/ Has component is true."""
        v = VariableCombinationItem(
            name="c",
            type=VariableType.CONTINUOUS,
            index=0,
            component_indices=(1, 2),
        )
        assert v.has_component(1) is True

    def test_has_component_false(self) -> None:
        """不包含组件判断为假。/ Has component is false."""
        v = VariableCombinationItem(
            name="c",
            type=VariableType.CONTINUOUS,
            index=0,
            component_indices=(1, 2),
        )
        assert v.has_component(99) is False


class TestVariableCombinationItemFactory:
    """工厂方法测试 / Factory method tests."""

    def test_from_indices_factory(self) -> None:
        """from_indices 工厂方法。/ from_indices factory."""
        v = VariableCombinationItem.from_indices(
            name="mix",
            index=5,
            component_indices=[10, 20, 30],
        )
        assert v.name == "mix"
        assert v.index == 5
        assert v.component_indices == (10, 20, 30)
        assert v.type is VariableType.CONTINUOUS

    def test_from_indices_with_type(self) -> None:
        """from_indices 指定类型。/ from_indices with type."""
        v = VariableCombinationItem.from_indices(
            name="int_mix",
            index=1,
            component_indices=[2, 3],
            type_=VariableType.INTEGER,
        )
        assert v.type is VariableType.INTEGER

    def test_is_frozen(self) -> None:
        """组合变量不可变。/ Combination is frozen."""
        v = VariableCombinationItem(
            name="c",
            type=VariableType.CONTINUOUS,
            index=0,
            component_indices=(1,),
        )
        with pytest.raises(AttributeError):
            v.name = "changed"  # type: ignore[misc]
