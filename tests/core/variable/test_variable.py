"""变量模块测试。

测试变量类型、变量范围、变量项及其子类。
Tests variable types, ranges, variable items, and subclasses.
"""

from __future__ import annotations

import pytest

from ospf_python.core.variable import (
    AbstractVariableItem,
    AnyVariable,
    VariableCombinationItem,
    VariableIndependentItem,
    VariableRange,
    VariableType,
)

# ---------------------------------------------------------------------------
# VariableType 测试
# ---------------------------------------------------------------------------


class TestVariableType:
    """变量类型枚举测试 / Variable type enum tests."""

    def test_continuous_value(self) -> None:
        """连续变量值正确。/ Continuous value is correct."""
        assert VariableType.CONTINUOUS.value == "continuous"

    def test_integer_value(self) -> None:
        """整数变量值正确。/ Integer value is correct."""
        assert VariableType.INTEGER.value == "integer"

    def test_binary_value(self) -> None:
        """二元变量值正确。/ Binary value is correct."""
        assert VariableType.BINARY.value == "binary"

    def test_semi_continuous_value(self) -> None:
        """半连续变量值正确。/ Semi-continuous value is correct."""
        assert VariableType.SEMI_CONTINUOUS.value == "semi_continuous"

    def test_semi_integer_value(self) -> None:
        """半整数变量值正确。/ Semi-integer value is correct."""
        assert VariableType.SEMI_INTEGER.value == "semi_integer"

    def test_all_types_count(self) -> None:
        """共 5 种变量类型。/ 5 variable types total."""
        assert len(VariableType) == 5

    def test_from_value(self) -> None:
        """通过值获取枚举。/ Get enum from value."""
        assert VariableType("continuous") is VariableType.CONTINUOUS


# ---------------------------------------------------------------------------
# VariableRange 测试
# ---------------------------------------------------------------------------


class TestVariableRange:
    """变量范围测试 / Variable range tests."""

    def test_create_default_range(self) -> None:
        """默认范围为 (-inf, inf)。/ Default range is (-inf, inf)."""
        r = VariableRange()
        assert r.lower == float("-inf")
        assert r.upper == float("inf")

    def test_create_bounded_range(self) -> None:
        """创建有界范围。/ Create bounded range."""
        r = VariableRange(lower=0.0, upper=10.0)
        assert r.lower == 0.0
        assert r.upper == 10.0

    def test_is_frozen(self) -> None:
        """范围不可变。/ Range is frozen."""
        r = VariableRange(lower=0.0, upper=1.0)
        with pytest.raises(AttributeError):
            r.lower = 2.0  # type: ignore[misc]

    def test_contains_value_in_range(self) -> None:
        """包含范围内的值。/ Contains value in range."""
        r = VariableRange(lower=0.0, upper=10.0)
        assert r.contains(5.0) is True

    def test_contains_boundary_value(self) -> None:
        """包含边界值。/ Contains boundary value."""
        r = VariableRange(lower=0.0, upper=10.0)
        assert r.contains(0.0) is True
        assert r.contains(10.0) is True

    def test_not_contains_out_of_range(self) -> None:
        """不包含范围外的值。/ Does not contain out-of-range."""
        r = VariableRange(lower=0.0, upper=10.0)
        assert r.contains(-1.0) is False
        assert r.contains(11.0) is False

    def test_width(self) -> None:
        """范围宽度正确。/ Range width is correct."""
        r = VariableRange(lower=2.0, upper=8.0)
        assert r.width == 6.0

    def test_is_unbounded(self) -> None:
        """无界范围判断。/ Unbounded range detection."""
        r = VariableRange()
        assert r.is_unbounded() is True

    def test_is_not_unbounded(self) -> None:
        """有界范围非无界。/ Bounded range is not unbounded."""
        r = VariableRange(lower=0.0, upper=1.0)
        assert r.is_unbounded() is False

    def test_non_negative_factory(self) -> None:
        """非负范围工厂方法。/ Non-negative factory method."""
        r = VariableRange.non_negative()
        assert r.lower == 0.0
        assert r.upper == float("inf")

    def test_unit_factory(self) -> None:
        """单位范围工厂方法。/ Unit range factory method."""
        r = VariableRange.unit()
        assert r.lower == 0.0
        assert r.upper == 1.0

    def test_fixed_factory(self) -> None:
        """固定值范围工厂方法。/ Fixed value factory method."""
        r = VariableRange.fixed(42.0)
        assert r.lower == 42.0
        assert r.upper == 42.0
        assert r.width == 0.0

    def test_create_factory(self) -> None:
        """create 工厂方法。/ create factory method."""
        r = VariableRange.create(lower=1.0, upper=5.0)
        assert r.lower == 1.0
        assert r.upper == 5.0

    def test_equality(self) -> None:
        """范围相等性。/ Range equality."""
        r1 = VariableRange(lower=0.0, upper=1.0)
        r2 = VariableRange(lower=0.0, upper=1.0)
        assert r1 == r2


# ---------------------------------------------------------------------------
# AnyVariable 测试
# ---------------------------------------------------------------------------


class TestAnyVariable:
    """通用变量测试 / AnyVariable tests."""

    def test_create_continuous(self) -> None:
        """创建连续变量。/ Create continuous variable."""
        v = AnyVariable.continuous(name="x", index=0, lower=0.0, upper=10.0)
        assert v.name == "x"
        assert v.index == 0
        assert v.type is VariableType.CONTINUOUS
        assert v.bounds.lower == 0.0
        assert v.bounds.upper == 10.0

    def test_create_integer(self) -> None:
        """创建整数变量。/ Create integer variable."""
        v = AnyVariable.integer(name="y", index=1)
        assert v.type is VariableType.INTEGER
        assert v.name == "y"

    def test_create_binary(self) -> None:
        """创建二元变量。/ Create binary variable."""
        v = AnyVariable.binary(name="b", index=2)
        assert v.type is VariableType.BINARY
        assert v.bounds.lower == 0.0
        assert v.bounds.upper == 1.0

    def test_is_frozen(self) -> None:
        """变量不可变。/ Variable is frozen."""
        v = AnyVariable.continuous(name="x", index=0)
        with pytest.raises(AttributeError):
            v.name = "changed"  # type: ignore[misc]

    def test_str_format(self) -> None:
        """字符串格式正确。/ String format is correct."""
        v = AnyVariable(
            name="x",
            type=VariableType.CONTINUOUS,
            index=5,
        )
        assert str(v) == "x[5](continuous)"

    def test_is_abstract_subclass(self) -> None:
        """是 AbstractVariableItem 子类。/ Is subclass."""
        v = AnyVariable.continuous(name="x", index=0)
        assert isinstance(v, AbstractVariableItem)


# ---------------------------------------------------------------------------
# VariableIndependentItem 测试
# ---------------------------------------------------------------------------


class TestVariableIndependentItem:
    """独立变量项测试 / Independent variable item tests."""

    def test_create_with_defaults(self) -> None:
        """默认参数创建。/ Create with defaults."""
        v = VariableIndependentItem(
            name="a",
            type=VariableType.CONTINUOUS,
            index=0,
        )
        assert v.name == "a"
        assert v.type is VariableType.CONTINUOUS

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


# ---------------------------------------------------------------------------
# VariableCombinationItem 测试
# ---------------------------------------------------------------------------


class TestVariableCombinationItem:
    """组合变量项测试 / Combination variable item tests."""

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

    def test_is_abstract_subclass(self) -> None:
        """是 AbstractVariableItem 子类。/ Is subclass."""
        v = VariableCombinationItem(
            name="c",
            type=VariableType.CONTINUOUS,
            index=0,
        )
        assert isinstance(v, AbstractVariableItem)
