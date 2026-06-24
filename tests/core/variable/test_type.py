"""VariableType 枚举测试。

测试变量类型枚举的定义、值和转换。
Tests VariableType enum definition, values, and conversion.
"""

from __future__ import annotations

import pytest

from ospf_python.core.variable.type import VariableType


class TestVariableTypeEnum:
    """变量类型枚举基础测试 / Basic enum tests."""

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
        """半连续变量值正确。/ Semi-continuous value correct."""
        assert VariableType.SEMI_CONTINUOUS.value == "semi_continuous"

    def test_semi_integer_value(self) -> None:
        """半整数变量值正确。/ Semi-integer value correct."""
        assert VariableType.SEMI_INTEGER.value == "semi_integer"

    def test_all_types_count(self) -> None:
        """共 5 种变量类型。/ 5 variable types total."""
        assert len(VariableType) == 5

    def test_from_value(self) -> None:
        """通过值获取枚举。/ Get enum from value."""
        assert VariableType("continuous") is VariableType.CONTINUOUS

    def test_invalid_value_raises(self) -> None:
        """无效值抛出 ValueError。/ Invalid value raises."""
        with pytest.raises(ValueError):
            VariableType("invalid")

    def test_is_enum_member(self) -> None:
        """枚举成员类型正确。/ Enum member type is correct."""
        assert isinstance(VariableType.BINARY, VariableType)

    def test_name_attribute(self) -> None:
        """枚举名称属性正确。/ Enum name attribute correct."""
        assert VariableType.CONTINUOUS.name == "CONTINUOUS"

    def test_iteration(self) -> None:
        """可遍历所有类型。/ Can iterate all types."""
        types = list(VariableType)
        assert len(types) == 5
