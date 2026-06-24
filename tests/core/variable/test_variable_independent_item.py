"""VariableIndependentItem 测试。

测试独立变量项的创建和类型判断方法。
Tests VariableIndependentItem creation and type checks.
"""

from __future__ import annotations

from ospf_python.core.variable.type import VariableType
from ospf_python.core.variable.variable_independent_item import (
    VariableIndependentItem,
)
from ospf_python.core.variable.variable_range import VariableRange


class TestVariableIndependentItemCreation:
    """创建测试 / Creation tests."""

    def test_create_with_defaults(self) -> None:
        """默认参数创建。/ Create with defaults."""
        v = VariableIndependentItem(
            name="a",
            type=VariableType.CONTINUOUS,
            index=0,
        )
        assert v.name == "a"
        assert v.type is VariableType.CONTINUOUS

    def test_with_bounds(self) -> None:
        """带范围创建。/ Create with bounds."""
        bounds = VariableRange(lower=0.0, upper=100.0)
        v = VariableIndependentItem(
            name="x",
            type=VariableType.CONTINUOUS,
            index=0,
            bounds=bounds,
        )
        assert v.bounds.lower == 0.0
        assert v.bounds.upper == 100.0


class TestVariableIndependentTypeChecks:
    """类型判断测试 / Type check tests."""

    def test_is_binary_true(self) -> None:
        """二元变量判断为真。/ Binary check is true."""
        v = VariableIndependentItem(
            name="b",
            type=VariableType.BINARY,
            index=0,
        )
        assert v.is_binary() is True

    def test_is_binary_false(self) -> None:
        """非二元变量判断为假。/ Non-binary check is false."""
        v = VariableIndependentItem(
            name="x",
            type=VariableType.CONTINUOUS,
            index=0,
        )
        assert v.is_binary() is False

    def test_is_integer_for_integer_type(self) -> None:
        """整数类型判断为真。/ Integer type check is true."""
        v = VariableIndependentItem(
            name="i",
            type=VariableType.INTEGER,
            index=0,
        )
        assert v.is_integer() is True

    def test_is_integer_for_binary(self) -> None:
        """二元类型视为整数。/ Binary type is integer."""
        v = VariableIndependentItem(
            name="b",
            type=VariableType.BINARY,
            index=0,
        )
        assert v.is_integer() is True

    def test_is_integer_for_semi_integer(self) -> None:
        """半整数类型视为整数。/ Semi-integer is integer."""
        v = VariableIndependentItem(
            name="s",
            type=VariableType.SEMI_INTEGER,
            index=0,
        )
        assert v.is_integer() is True

    def test_is_continuous_true(self) -> None:
        """连续类型判断为真。/ Continuous check is true."""
        v = VariableIndependentItem(
            name="x",
            type=VariableType.CONTINUOUS,
            index=0,
        )
        assert v.is_continuous() is True

    def test_is_continuous_false(self) -> None:
        """非连续类型判断为假。/ Non-continuous is false."""
        v = VariableIndependentItem(
            name="i",
            type=VariableType.INTEGER,
            index=0,
        )
        assert v.is_continuous() is False
